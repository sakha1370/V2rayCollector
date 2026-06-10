import os

from test_mtproto_proxies import deduplicate_proxies


def main():
    input_file = "mtproto_iran.txt"

    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found, skipping deduplication.")
        return

    # Read existing proxies (skip comments and empty lines)
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.lstrip().startswith("#")]

    if not lines:
        print("No proxies found in input file, nothing to deduplicate.")
        return

    # Use the same deduplication logic as in tests
    unique_proxies = deduplicate_proxies(lines)

    # Overwrite the file with clean, unique proxies
    with open(input_file, "w", encoding="utf-8") as f:
        for proxy in unique_proxies:
            f.write(proxy + "\n")

    print(f"Deduplicated MTProto proxies written to '{input_file}'. Total unique proxies: {len(unique_proxies)}")


if __name__ == "__main__":
    main()

