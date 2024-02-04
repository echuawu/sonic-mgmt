import re


def parse_ip_address_from_packet(ip_string):
    """
    A function that extracts the actual ip address from the wjh table entry, so the WJH entry validation will be simple.
     Handles both IPv4 and IPv6 addresses.
     Example:
        For IPv4, taking the <ipv4_addr:port> wjh entry and extracts the ipv4_addr.
        For IPv6, take the <[ipv6_addr]:port> and extract the ipv6_addr.
    :param ip_string: The entry from wjh_table containing the ip address and the port
    """
    # Patterns for matching the ip addresses and their ports (optional)
    ipv4_pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+):?(\d+)?')
    ipv6_pattern = re.compile(r'\[?([0-9a-fA-F:]+)\]?:?(\d+)?')

    ipv4_match = ipv4_pattern.match(ip_string)
    if ipv4_match:
        ip = ipv4_match.group(1)
        return ip

    ipv6_match = ipv6_pattern.match(ip_string)
    if ipv6_match:
        ip = ipv6_match.group(1)
        return ip

    # Return N/A if the input doesn't match one of the patterns
    return 'N/A'
