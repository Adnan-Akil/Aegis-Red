"""
src/utils/ssrf_guard.py

Target URL SSRF (Server-Side Request Forgery) protection and validation module.
Validates scan target URLs to prevent attacks against internal infrastructure or cloud metadata endpoints.
"""
import logging
import os
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Cloud instance metadata & special dangerous IP targets (ALWAYS blocked)
ALWAYS_BLOCKED_IPS = {
    "169.254.169.254",  # AWS/GCP/Azure Metadata
    "168.63.129.16",   # Azure WireServer
    "100.100.100.200",  # Alibaba Metadata
    "0.0.0.0",
}

# Private IP subnets (RFC 1918 / RFC 6598 / Loopback)
PRIVATE_IP_PREFIXES = (
    "10.",          # 10.0.0.0/8
    "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.",
    "172.24.", "172.25.", "172.26.", "172.27.",
    "172.28.", "172.29.", "172.30.", "172.31.", # 172.16.0.0/12
    "192.168.",     # 192.168.0.0/16
    "100.64.",      # CGNAT 100.64.0.0/10
)

LOOPBACK_PREFIXES = ("127.", "::1", "fe80:")


def validate_target_url(url: str) -> tuple[bool, str | None]:
    """
    Validates a scan target URL against SSRF rules.
    Returns (is_valid: bool, error_message: str | None).
    
    Rules:
    1. Scheme must be http or https.
    2. Cloud metadata endpoints (169.254.169.254) are ALWAYS BLOCKED.
    3. Localhost (127.0.0.1 / localhost) is PERMITTED in development mode (ENVIRONMENT=development
       or ALLOW_PRIVATE_TARGETS=true) to enable local AI application testing.
    4. Private RFC1918 IPs are blocked in production unless ALLOW_PRIVATE_TARGETS=true.
    """
    if not url or not isinstance(url, str):
        return False, "Target URL must be a non-empty string."

    url_str = url.strip()
    if not url_str.startswith(("http://", "https://")):
        return False, "Target URL must start with http:// or https://"

    try:
        parsed = urlparse(url_str)
        hostname = parsed.hostname
        if not hostname:
            return False, "Target URL is missing a valid domain or IP hostname."
        
        hostname_lower = hostname.lower()

        # Check explicit Cloud Metadata block
        if hostname_lower in ALWAYS_BLOCKED_IPS:
            return False, f"Target IP '{hostname}' is a reserved Cloud Metadata endpoint and is strictly prohibited."

        # Environment configuration flags
        env_mode = os.getenv("ENVIRONMENT", "development").lower()
        allow_private = os.getenv("ALLOW_PRIVATE_TARGETS", "true" if env_mode == "development" else "false").lower() == "true"

        # Resolve IP address
        try:
            resolved_ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            # If hostname cannot be resolved, allow HTTP driver to attempt connection error handling
            resolved_ip = None

        if resolved_ip and resolved_ip in ALWAYS_BLOCKED_IPS:
            return False, f"Target host '{hostname}' resolved to prohibited IP '{resolved_ip}'."

        # Localhost / Loopback check
        is_localhost = hostname_lower in ("localhost", "127.0.0.1", "::1") or (resolved_ip and resolved_ip.startswith(LOOPBACK_PREFIXES))

        if is_localhost:
            if allow_private:
                logger.info(f"Localhost target '{url_str}' permitted under development mode (ALLOW_PRIVATE_TARGETS=true).")
                return True, None
            else:
                return False, f"Scanning localhost ('{hostname}') is restricted in production mode."

        # General Private IP check (RFC 1918)
        if resolved_ip and resolved_ip.startswith(PRIVATE_IP_PREFIXES):
            if not allow_private:
                return False, f"Target IP '{resolved_ip}' belongs to a private network subnet and is blocked in production."

        return True, None

    except Exception as e:
        logger.error(f"Error validating target URL '{url}': {e!s}")
        return False, f"Invalid target URL structure: {e!s}"

