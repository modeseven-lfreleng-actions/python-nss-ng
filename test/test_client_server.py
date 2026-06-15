# SPDX-License-Identifier: MPL-2.0
# SPDX-FileCopyrightText: Copyright (c) 2010-2025 python-nss-ng contributors

# This integration test exercises the legacy NSPR socket / SSL APIs
# directly: it imports a plain TCP socket via ``io.Socket.import_tcp_socket``
# and then assigns the resulting object back into an ``ssl.SSLSocket``-typed
# variable, and similarly mixes ``str`` and ``bytes`` payloads on send/recv.
# Modernising the code to satisfy strict mypy would change observable
# behaviour and is out of scope for the tooling sync.
#
# mypy: ignore-errors

import contextlib
import getpass
import os
import platform
import socket
import sys
import threading

import pytest

import nss.io as io
import nss.nss as nss
import nss.ssl as ssl
from nss.error import NSPRError

# -----------------------------------------------------------------------------
NO_CLIENT_CERT = 0
REQUEST_CLIENT_CERT_ONCE = 1
REQUIRE_CLIENT_CERT_ONCE = 2
REQUEST_CLIENT_CERT_ALWAYS = 3
REQUIRE_CLIENT_CERT_ALWAYS = 4

verbose = True
info = True
password = "DB_passwd"
use_ssl = True
client_cert_action = NO_CLIENT_CERT

# Use localhost instead of system hostname for reliable resolution across all platforms
# This is especially important for CI environments where system hostnames may not resolve
hostname = "localhost"
server_nickname = "test_server"
client_nickname = "test_user"
timeout_secs = 10
server_ready = threading.Event()
port = 0  # Will be set by test functions


# -----------------------------------------------------------------------------
# Callback Functions
# -----------------------------------------------------------------------------


def password_callback(slot, retry, password):
    if password:
        return password
    return getpass.getpass("Enter password: ")


def handshake_callback(sock):
    if verbose:
        print("-- handshake complete --")
        print("peer: %s" % (sock.get_peer_name()))
        print("negotiated host: %s" % (sock.get_negotiated_host()))
        print()
        print(sock.connection_info_str())
        print("-- handshake complete --")
        print()


def auth_certificate_callback(sock, check_sig, is_server, certdb):
    if verbose:
        print("auth_certificate_callback: check_sig=%s is_server=%s" % (check_sig, is_server))
    cert_is_valid = False

    cert = sock.get_peer_certificate()
    pin_args = sock.get_pkcs11_pin_arg()
    if pin_args is None:
        pin_args = ()

    # if verbose:
    #    print("cert:\n%s" % cert)

    # Define how the cert is being used based upon the is_server flag.  This may
    # seem backwards, but isn't. If we're a server we're trying to validate a
    # client cert. If we're a client we're trying to validate a server cert.
    if is_server:
        intended_usage = nss.certificateUsageSSLClient
    else:
        intended_usage = nss.certificateUsageSSLServer

    try:
        # If the cert fails validation it will raise an exception, the errno attribute
        # will be set to the error code matching the reason why the validation failed
        # and the strerror attribute will contain a string describing the reason.
        approved_usage = cert.verify_now(certdb, check_sig, intended_usage, *pin_args)
    except Exception as e:
        print("auth_certificate_callback: %s" % e, file=sys.stderr)
        cert_is_valid = False
        if verbose:
            print("Returning cert_is_valid = %s" % cert_is_valid)
        return cert_is_valid

    if verbose:
        print("approved_usage = %s" % ", ".join(nss.cert_usage_flags(approved_usage)))

    # Is the intended usage a proper subset of the approved usage
    if approved_usage & intended_usage:
        cert_is_valid = True
    else:
        cert_is_valid = False

    # If this is a server, we're finished
    if is_server or not cert_is_valid:
        if verbose:
            print("Returning cert_is_valid = %s" % cert_is_valid)
        return cert_is_valid

    # Certificate is OK.  Since this is the client side of an SSL
    # connection, we need to verify that the name field in the cert
    # matches the desired hostname.  This is our defense against
    # man-in-the-middle attacks.

    hostname = sock.get_hostname()
    if verbose:
        print("verifying socket hostname (%s) matches cert subject (%s)" % (hostname, cert.subject))
    try:
        # If the cert fails validation it will raise an exception
        cert_is_valid = cert.verify_hostname(hostname)
    except Exception as e:
        print("auth_certificate_callback: %s" % e, file=sys.stderr)
        cert_is_valid = False
        if verbose:
            print("Returning cert_is_valid = %s" % cert_is_valid)
        return cert_is_valid

    if verbose:
        print("Returning cert_is_valid = %s" % cert_is_valid)
    return cert_is_valid


def client_auth_data_callback(ca_names, chosen_nickname, password, certdb):
    cert = None
    if chosen_nickname:
        try:
            cert = nss.find_cert_from_nickname(chosen_nickname, password)
            priv_key = nss.find_key_by_any_cert(cert, password)
            if verbose:
                print("client cert:\n%s" % cert)
            return cert, priv_key
        except NSPRError as e:
            print("client_auth_data_callback: %s" % e, file=sys.stderr)
            return False
    else:
        nicknames = nss.get_cert_nicknames(certdb, nss.SEC_CERT_NICKNAMES_USER)
        for nickname in nicknames:
            try:
                cert = nss.find_cert_from_nickname(nickname, password)
                if verbose:
                    print("client cert:\n%s" % cert)
                if cert.check_valid_times():
                    if cert.has_signer_in_ca_names(ca_names):
                        priv_key = nss.find_key_by_any_cert(cert, password)
                        return cert, priv_key
            except NSPRError as e:
                print("client_auth_data_callback: %s" % e, file=sys.stderr)
        return False


# -----------------------------------------------------------------------------
# Client Implementation
# -----------------------------------------------------------------------------


def client(request, test_port):
    if use_ssl:
        if info:
            print("client: using SSL")
        ssl.set_domestic_policy()

    # Get the IP Address of our server
    try:
        addr_info = io.AddrInfo(hostname)
    except Exception:
        print('client: could not resolve host address "%s"' % hostname, file=sys.stderr)
        return None

    for net_addr in addr_info:
        net_addr.port = test_port

        if use_ssl:
            sock = ssl.SSLSocket(net_addr.family)

            # Set client SSL socket options
            sock.set_ssl_option(ssl.SSL_SECURITY, True)
            sock.set_ssl_option(ssl.SSL_HANDSHAKE_AS_CLIENT, True)
            sock.set_hostname(hostname)

            # Provide a callback which notifies us when the SSL handshake is complete
            sock.set_handshake_callback(handshake_callback)

            # Provide a callback to supply our client certificate info
            sock.set_client_auth_data_callback(
                client_auth_data_callback, client_nickname, password, nss.get_default_certdb()
            )

            # Provide a callback to verify the servers certificate
            sock.set_auth_certificate_callback(auth_certificate_callback, nss.get_default_certdb())
        else:
            sock = io.Socket(net_addr.family)

        try:
            if verbose:
                print("client trying connection to: %s" % (net_addr))
            sock.connect(net_addr, timeout=io.seconds_to_interval(timeout_secs))
            if verbose:
                print("client connected to: %s" % (net_addr))
            break
        except Exception as e:
            sock.close()
            print("client: connection to: %s failed (%s)" % (net_addr, e), file=sys.stderr)

    # Talk to the server
    try:
        if info:
            print('client: sending "%s"' % (request))
        data = request + "\n"  # newline is protocol record separator
        sock.send(data.encode("utf-8"))
        buf = sock.readline()
        if not buf:
            print("client: lost connection", file=sys.stderr)
            sock.close()
            return None
        buf = buf.decode("utf-8")
        buf = buf.rstrip()  # remove newline record separator
        if info:
            print('client: received "%s"' % (buf))
    except Exception as e:
        print("client: %s" % e, file=sys.stderr)
        with contextlib.suppress(NSPRError, OSError):
            sock.close()
        return None

    try:
        sock.shutdown()
    except Exception as e:
        print("client: %s" % e, file=sys.stderr)

    try:
        sock.close()
        if use_ssl:
            ssl.clear_session_cache()
    except Exception as e:
        print("client: %s" % e, file=sys.stderr)

    return buf


# -----------------------------------------------------------------------------
# Server Implementation
# -----------------------------------------------------------------------------


def get_free_port():
    """Get a free port by binding to port 0 and letting the OS choose.

    Note: This function creates and closes a socket to get a free port.
    There's a small race condition window where another process could grab
    the port, but this is unavoidable with this approach. The server binding
    happens quickly enough that this is rarely an issue in practice.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def server(test_port):
    if verbose:
        print("starting server:")

    # Initialize
    # Setup an IP Address to listen on the loopback interface only.
    # The tests are entirely local (the client connects via localhost),
    # so there is no need to listen on all interfaces.
    net_addr = io.NetworkAddress(io.PR_IpAddrLoopback, test_port)

    if use_ssl:
        if info:
            print("server: using SSL")
        ssl.set_domestic_policy()
        nss.set_password_callback(password_callback)

        # Perform basic SSL server configuration
        # Enforce minimum TLS 1.2 for security
        ssl.set_default_ssl_version_range(
            ssl.SSL_LIBRARY_VERSION_TLS_1_2, ssl.SSL_LIBRARY_VERSION_TLS_1_3
        )
        ssl.config_server_session_id_cache()

        # Get our certificate and private key
        server_cert = nss.find_cert_from_nickname(server_nickname, password)
        priv_key = nss.find_key_by_any_cert(server_cert, password)
        server_cert_kea = server_cert.find_kea_type()

        # if verbose:
        #    print("server cert:\n%s" % server_cert)

        sock = ssl.SSLSocket(net_addr.family)

        # Set server SSL socket options
        sock.set_pkcs11_pin_arg(password)
        sock.set_ssl_option(ssl.SSL_SECURITY, True)
        sock.set_ssl_option(ssl.SSL_HANDSHAKE_AS_SERVER, True)

        # If we're doing client authentication then set it up
        if client_cert_action >= REQUEST_CLIENT_CERT_ONCE:
            sock.set_ssl_option(ssl.SSL_REQUEST_CERTIFICATE, True)
        if client_cert_action == REQUIRE_CLIENT_CERT_ONCE:
            sock.set_ssl_option(ssl.SSL_REQUIRE_CERTIFICATE, True)
        sock.set_auth_certificate_callback(auth_certificate_callback, nss.get_default_certdb())

        # Configure the server SSL socket
        sock.config_secure_server(server_cert, priv_key, server_cert_kea)

    else:
        sock = io.Socket(net_addr.family)

    # Bind to our network address and listen for clients
    sock.bind(net_addr)
    if verbose:
        print("listening on: %s" % (net_addr))
    sock.listen()

    # Signal that server is ready - do this AFTER listen() completes
    # to ensure the socket is fully ready to accept connections
    server_ready.set()

    # Small delay to ensure the listening socket is fully established
    # This helps prevent race conditions on ARM64 where timing is different
    import time

    time.sleep(0.1)

    # Accept a single connection from a client
    client_sock, client_addr = sock.accept()
    if use_ssl:
        client_sock.set_handshake_callback(handshake_callback)

    if verbose:
        print("client connect from: %s" % (client_addr))

    try:
        # Handle the client connection
        buf = client_sock.readline()  # newline is protocol record separator
        if not buf:
            print("server: lost connection to %s" % (client_addr), file=sys.stderr)
        else:
            buf = buf.decode("utf-8")
            buf = buf.rstrip()  # remove newline record separator

            if info:
                print('server: received "%s"' % (buf))
            reply = "{%s}" % buf  # echo embedded inside braces
            if info:
                print('server: sending "%s"' % (reply))
            data = reply + "\n"  # send echo with record separator
            client_sock.send(data.encode("utf-8"))

        with contextlib.suppress(NSPRError, OSError):
            client_sock.shutdown()
        client_sock.close()
    except Exception as e:
        print("server: %s" % e, file=sys.stderr)
        with contextlib.suppress(NSPRError, OSError):
            client_sock.close()

    # Clean up
    with contextlib.suppress(NSPRError, OSError):
        sock.shutdown()
    sock.close()
    if use_ssl:
        ssl.shutdown_server_session_id_cache()


# -----------------------------------------------------------------------------


def run_server_thread(port):
    """Run server in a background thread with proper error handling."""
    server_ready.clear()

    # Store exception from server thread if it crashes
    server_exception = []

    def server_wrapper(port):
        try:
            server(port)
        except Exception as e:
            server_exception.append(e)
            raise

    thread = threading.Thread(target=server_wrapper, args=(port,), daemon=True)
    thread.start()

    # Wait for server to be ready (with timeout)
    # The server_ready event is set when the server is listening,
    # which is the deterministic signal we need
    if not server_ready.wait(timeout=5):
        if server_exception:
            raise RuntimeError(f"Server crashed during startup: {server_exception[0]}")
        raise RuntimeError("Server failed to start within timeout")

    # Additional small delay to ensure socket is fully ready on all architectures
    import time

    time.sleep(0.2)

    return thread


def _should_skip_ssl_threading_test():
    """Check if SSL threading test should be skipped on this platform."""
    # Skip on macOS - known NSS threading issues
    if platform.system() == "Darwin":
        return True

    # Skip in CI environments - NSS SSL threading has known race conditions
    # that cause intermittent segfaults, especially with ssl.shutdown_server_session_id_cache()
    if os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true":
        return True

    # Skip on Linux ARM64 with NSS < 3.119 - threading segfaults
    if platform.system() == "Linux" and platform.machine() in ("aarch64", "arm64"):
        try:
            import nss.nss as nss

            version_str = nss.nss_get_version()
            # Parse version like "3.118" or "3.118.1" -> [3, 118, ...]
            # Pad with zeros for comparison: [3, 118] -> [3, 118, 0]
            version_parts = [int(x) for x in version_str.split(".")]
            version_parts += [0] * (3 - len(version_parts))  # Pad to 3 parts
            if version_parts < [3, 119, 0]:
                return True
        except Exception:
            # If we can't determine version, skip to be safe
            return True

    return False


class TestSSL:
    """Test SSL client-server communication."""

    @pytest.mark.xdist_group("ssl_serial")
    @pytest.mark.skipif(
        _should_skip_ssl_threading_test(),
        reason="NSS SSL threading causes segfault on this platform/version due to known NSS library threading issues",
    )
    def test_ssl(self, nss_db_context):
        """Test SSL client-server communication using threading.

        Note: This test is skipped on platforms with known NSS threading issues:
        - macOS: All versions
        - CI environments: All (intermittent segfaults in ssl.shutdown_server_session_id_cache)
        - Linux ARM64: NSS < 3.119

        These segmentation faults occur when performing SSL handshakes in multiple
        threads simultaneously, particularly during session cache shutdown. This is
        a limitation of the underlying NSS library, not the python-nss-ng bindings.
        """
        # Get a free port for this test
        global port
        port = get_free_port()

        # NSS is already initialized by nss_db_context fixture

        # Start server in background thread
        server_thread = run_server_thread(port)

        # Run client
        request = "foo"
        reply = client(request, port)

        # Verify response
        assert "{%s}" % request == reply

        # Wait for server thread to complete
        server_thread.join(timeout=5)

        # Check if server thread is still alive (shouldn't be)
        if server_thread.is_alive():
            raise RuntimeError("Server thread did not complete within timeout")

        # NSS cleanup happens automatically in fixture teardown
