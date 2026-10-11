"""Small HTTP adapter for Evolution GO's instance-token API."""

from __future__ import annotations

import time
from urllib.parse import quote


_instance_cache = {}
_CACHE_SECONDS = 30


def _request(method, url, token, *, json=None, timeout=12):
    headers = {"apikey": token, "Content-Type": "application/json"}
    try:
        import httpx
        response = httpx.request(method, url, headers=headers, json=json, timeout=timeout)
    except ImportError:
        import requests
        response = requests.request(method, url, headers=headers, json=json, timeout=timeout)
    response.raise_for_status()
    return response.json() if response.text else {}


def get_instance(cfg):
    base = str(cfg.get("api_url") or "http://127.0.0.1:8766").strip().rstrip("/")
    admin_key = str(cfg.get("api_token") or "").strip()
    name = str(cfg.get("instance_id") or "").strip()
    if not admin_key or not name:
        raise ValueError("Configure a chave global e o nome da instância Evolution GO.")
    key = (base, admin_key, name)
    cached = _instance_cache.get(key)
    if cached and cached[0] > time.monotonic():
        return base, cached[1]
    result = _request("GET", f"{base}/instance/all", admin_key, timeout=8)
    instances = result.get("data", []) if isinstance(result, dict) else []
    if not isinstance(instances, list):
        instances = []
    instance = next((row for row in instances if isinstance(row, dict) and row.get("name") == name), None)
    if not instance:
        raise ValueError(f"Instância Evolution GO '{name}' não encontrada ou sem token.")
    if not instance.get("token"):
        instance_id = quote(str(instance.get("id") or name), safe="")
        info = _request("GET", f"{base}/instance/info/{instance_id}", admin_key, timeout=8)
        detail = info.get("data", {}) if isinstance(info, dict) else {}
        if isinstance(detail, dict) and detail.get("name") in (None, name):
            instance = detail
    if not instance.get("token"):
        raise ValueError(f"Instância Evolution GO '{name}' encontrada, mas não foi possível obter o token interno.")
    _instance_cache[key] = (time.monotonic() + _CACHE_SECONDS, instance)
    return base, instance


def instance_request(cfg, method, path, *, json=None, timeout=12):
    base, instance = get_instance(cfg)
    return _request(method, f"{base}{path}", str(instance["token"]), json=json, timeout=timeout)


def send_text(phone, text, cfg):
    base, instance = get_instance(cfg)
    number = "".join(ch for ch in str(phone) if ch.isdigit())
    return _request(
        "POST", f"{base}/send/text", str(instance["token"]),
        json={"number": number, "text": text}, timeout=20,
    )


def clear_instance_cache():
    _instance_cache.clear()


__all__ = ["get_instance", "instance_request", "send_text", "clear_instance_cache"]
