import ipaddress


def _is_trusted_proxy_host(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_loopback or ip.is_private
    except Exception:
        return False


def _client_ip(request) -> str:
    """Pega IP real apenas quando o request veio de proxy local/confiavel."""
    try:
        direct = request.client.host if request.client else "?"
        if _is_trusted_proxy_host(direct):
            xff = request.headers.get("x-forwarded-for", "")
            if xff: return xff.split(",")[0].strip()
            xreal = request.headers.get("x-real-ip", "")
            if xreal: return xreal.strip()
        return direct
    except Exception:
        return "?"
