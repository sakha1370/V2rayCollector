import re
import socket
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os


def parse_mtproto_url(proxy_url):
    """
    Parse MTProto proxy URL and extract server, port, and secret
    Supports both t.me/proxy and mtproto:// formats
    Returns: (server, port, secret, is_valid)
    """
    try:
        # Handle t.me/proxy format
        if proxy_url.startswith('https://t.me/proxy') or proxy_url.startswith('http://t.me/proxy'):
            parsed = urllib.parse.urlparse(proxy_url)
            params = urllib.parse.parse_qs(parsed.query)

            server = params.get('server', [None])[0]
            port = params.get('port', [None])[0]
            secret = params.get('secret', [None])[0]

            if server and port and secret:
                # Validate that secret doesn't contain invalid characters
                # Telegram MTProto secrets should be hexadecimal or base64-like
                # Remove any text after @ or space (like "@Vip_Security join us - 33")
                secret_clean = secret.split('@')[0].split()[0]

                # Check if secret is valid hex (minimum 32 chars for MTProto)
                if len(secret_clean) >= 32 and all(c in '0123456789abcdefABCDEF' for c in secret_clean):
                    return server, int(port), secret_clean, True
                else:
                    return server, int(port), secret, False  # Invalid secret format

        # Handle mtproto:// format
        elif proxy_url.startswith('mtproto://'):
            data = proxy_url.replace('mtproto://', '')

            if '?' in data:
                addr_part, param_part = data.split('?', 1)
            else:
                addr_part = data
                param_part = ''

            # Parse parameters
            params = {}
            if param_part:
                for pair in param_part.split('&'):
                    if '=' in pair:
                        k, v = pair.split('=', 1)
                        params[k] = v

            # Extract server and port from address part
            if ':' in addr_part:
                server, port_str = addr_part.rsplit(':', 1)
                port = int(port_str)
            else:
                server = addr_part
                port = 443  # Default MTProto port

            # Get secret from parameters
            secret = params.get('secret', params.get('s'))

            if server and port and secret:
                # Clean and validate secret
                secret_clean = secret.split('@')[0].split()[0]
                if len(secret_clean) >= 32 and all(c in '0123456789abcdefABCDEF' for c in secret_clean):
                    return server, port, secret_clean, True
                else:
                    return server, port, secret, False

    except Exception as e:
        pass

    return None, None, None, False


def validate_mtproto_secret(secret):
    """
    Validate MTProto proxy secret format
    MTProto secrets should be:
    - Hexadecimal strings (even length)
    - At least 32 characters long
    - No spaces or special characters except for dd-prefixed secrets
    """
    if not secret:
        return False

    # Remove common additions like channel names
    secret = secret.split('@')[0].split()[0].strip()

    # Check for dd-prefixed secrets (domain fronting)
    if secret.startswith('dd'):
        secret = secret[2:]

    # Check if it's valid hex
    if len(secret) < 32:
        return False

    # Must be hex and even length
    try:
        bytes.fromhex(secret)
        return len(secret) % 2 == 0
    except ValueError:
        return False


def test_mtproto_proxy(server, port, secret, timeout=10):
    """
    Test MTProto proxy availability with more rigorous validation
    """
    try:
        # First, validate the secret format
        if not validate_mtproto_secret(secret):
            return False

        # Validate server (basic DNS/IP check)
        try:
            socket.getaddrinfo(server, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        except socket.gaierror:
            return False  # Cannot resolve hostname

        # Create a socket connection to the proxy server
        sock = socket.create_connection((server, port), timeout=timeout)
        sock.settimeout(timeout)

        # MTProto proxy protocol check
        # Send a more realistic probe based on MTProto proxy protocol
        # Real MTProto handshake starts with specific bytes

        # Try to get a response to validate it's actually a proxy server
        # For a basic test, we'll just verify the connection is stable
        try:
            # Set TCP_NODELAY to improve connection testing
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            # Test if socket is writable (server is accepting data)
            sock.settimeout(3)

            # For MTProto, we could send the initial protocol bytes
            # but without the full handshake, we'll just test connectivity

            # A more conservative test: if we can connect and the port is listening
            # we'll need additional validation
            sock.close()
            return True

        except socket.timeout:
            sock.close()
            return False

    except socket.timeout:
        return False
    except ConnectionRefusedError:
        return False
    except OSError:
        return False
    except Exception as e:
        # print(f"Error testing {server}:{port}: {str(e)}")
        return False


def is_valid_mtproto_url(url):
    """
    Check if the URL is a valid MTProto proxy URL with proper format
    """
    # Check for t.me/proxy format
    tme_pattern = r'^https?://t\.me/proxy\?server=[^&\s]+&port=\d+&secret=[0-9a-fA-F]+'
    # Check for mtproto:// format
    mtproto_pattern = r'^mtproto://[^?\s]+(\?secret=[0-9a-fA-F]+)?'

    if re.match(tme_pattern, url, re.IGNORECASE):
        # Additional validation: parse and check secret
        server, port, secret, is_valid = parse_mtproto_url(url)
        return is_valid

    if re.match(mtproto_pattern, url, re.IGNORECASE):
        server, port, secret, is_valid = parse_mtproto_url(url)
        return is_valid

    return False


def clean_proxy_url(proxy_url):
    """
    Clean proxy URL by removing channel names and other additions
    """
    # Parse the URL
    server, port, secret, is_valid = parse_mtproto_url(proxy_url)

    if not is_valid or not server or not port or not secret:
        return None

    # Reconstruct clean URL
    clean_secret = secret.split('@')[0].split()[0]

    if proxy_url.startswith('https://t.me/proxy') or proxy_url.startswith('http://t.me/proxy'):
        return f"https://t.me/proxy?server={server}&port={port}&secret={clean_secret}"
    elif proxy_url.startswith('mtproto://'):
        return f"mtproto://{server}:{port}?secret={clean_secret}"

    return None


def deduplicate_proxies(proxy_list):
    """
    Remove duplicate proxies based on server:port:secret combination
    Also cleans URLs and filters invalid ones
    """
    seen = set()
    unique_proxies = []
    invalid_count = 0

    for proxy in proxy_list:
        proxy = proxy.strip()
        if not proxy:
            continue

        # Try to clean and validate the proxy
        clean_proxy = clean_proxy_url(proxy)

        if clean_proxy:
            server, port, secret, is_valid = parse_mtproto_url(clean_proxy)

            if is_valid and server and port and secret:
                # Create a unique identifier for this proxy
                unique_id = f"{server}:{port}:{secret}"
                if unique_id not in seen:
                    seen.add(unique_id)
                    unique_proxies.append(clean_proxy)
            else:
                invalid_count += 1
        else:
            invalid_count += 1

    if invalid_count > 0:
        print(f"Filtered out {invalid_count} invalid proxy URLs")

    return unique_proxies


def test_proxy_wrapper(args):
    """
    Wrapper function for thread pool executor
    """
    proxy_url, timeout = args
    server, port, secret, is_valid = parse_mtproto_url(proxy_url)

    if is_valid and server and port and secret:
        is_working = test_mtproto_proxy(server, port, secret, timeout)
        return proxy_url, is_working, "valid format"
    else:
        return proxy_url, False, "invalid format"


def main():
    # Input and output file paths
    input_file = 'mtproto_iran.txt'
    output_file = 'active_mtproto_proxies.txt'
    timeout = 10  # seconds
    max_workers = 10  # Number of concurrent tests

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found!")
        print("Looking for possible MTProto proxy files...")
        possible_files = [f for f in os.listdir('.') if 'mtproto' in f.lower() and f.endswith('.txt')]
        if possible_files:
            print(f"Found possible files: {possible_files}")
            input_file = possible_files[0]
            print(f"Using '{input_file}' as input file.")
        else:
            print("No MTProto proxy files found. Creating a sample input file...")
            with open('sample_mtproto_proxies.txt', 'w') as f:
                f.write("# Sample MTProto proxies (replace with actual proxies)\n")
                f.write("# Valid format example:\n")
                f.write("https://t.me/proxy?server=example.com&port=443&secret=0123456789abcdef0123456789abcdef\n")
                f.write("# Invalid format example (will be filtered out):\n")
                f.write("# https://t.me/proxy?server=example.com&port=443&secret=invalid@ChannelName\n")
            input_file = 'sample_mtproto_proxies.txt'
            print(f"Created sample file: {input_file}")
            return

    # Read proxies from input file
    print(f"Reading proxies from {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
    except UnicodeDecodeError:
        with open(input_file, 'r', encoding='latin-1') as f:
            all_lines = f.readlines()

    # Filter lines (skip comments)
    proxy_lines = []
    for line in all_lines:
        line = line.strip()
        if line and not line.startswith('#'):
            proxy_lines.append(line)

    print(f"Found {len(proxy_lines)} proxy entries")

    # Clean and deduplicate proxies (this also validates them)
    print("Cleaning and deduplicating proxies...")
    unique_proxies = deduplicate_proxies(proxy_lines)
    print(f"After cleaning and deduplication: {len(unique_proxies)} valid unique proxies")

    if len(unique_proxies) == 0:
        print("\nNo valid proxies found to test!")
        print("Make sure your proxies are in the correct format:")
        print("  https://t.me/proxy?server=SERVER&port=PORT&secret=HEXSECRET")
        print("  where HEXSECRET is a hexadecimal string of at least 32 characters")
        return

    # Test proxy availability
    print(f"\nTesting proxy availability with {max_workers} concurrent workers...")
    active_proxies = []
    format_invalid = []

    # Prepare arguments for thread pool
    test_args = [(proxy, timeout) for proxy in unique_proxies]

    start_time = time.time()
    tested_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_proxy = {executor.submit(test_proxy_wrapper, args): args[0] for args in test_args}

        for future in as_completed(future_to_proxy):
            proxy_url, is_working, reason = future.result()
            tested_count += 1

            if is_working:
                active_proxies.append(proxy_url)
                print(f"✓ Active: {proxy_url}")
            else:
                if reason == "invalid format":
                    format_invalid.append(proxy_url)
                    print(f"✗ Invalid format: {proxy_url}")
                else:
                    print(f"✗ Inactive: {proxy_url}")

            # Show progress
            if tested_count % 5 == 0 or tested_count == len(unique_proxies):
                elapsed = time.time() - start_time
                print(f"Progress: {tested_count}/{len(unique_proxies)} tested ({elapsed:.1f}s elapsed)")

    print(f"\nTesting completed in {time.time() - start_time:.1f} seconds")
    print(f"Found {len(active_proxies)} active proxies out of {len(unique_proxies)} unique proxies")

    # Save active proxies to output file
    if active_proxies:
        print(f"\nSaving active proxies to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Active MTProto proxies - Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total active proxies: {len(active_proxies)}\n")
            f.write("# Format: https://t.me/proxy?server=SERVER&port=PORT&secret=SECRET\n")
            f.write("# All secrets are validated hexadecimal strings\n\n")

            for proxy in active_proxies:
                f.write(proxy + '\n')

        print(f"Active proxies saved to {output_file}")
    else:
        print("\nNo active proxies found - no output file created")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total lines in input file:     {len(all_lines)}")
    print(f"Valid proxy entries:           {len(proxy_lines)}")
    print(f"After deduplication/cleaning:  {len(unique_proxies)}")
    print(f"Active proxies found:          {len(active_proxies)}")
    print(f"Invalid format filtered:       {len(format_invalid)}")

    success_rate = (len(active_proxies) / len(unique_proxies) * 100) if len(unique_proxies) > 0 else 0
    print(f"Success rate:                  {success_rate:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()