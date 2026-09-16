import re
import unicodedata


def normalize_seller_name(name):
    display = re.sub(r"\s+", " ", str(name or "").strip())
    if not display:
        raise ValueError("Nome do vendedor obrigatorio.")
    if not any(ch.isalnum() for ch in display):
        raise ValueError("Nome do vendedor invalido.")
    key = unicodedata.normalize("NFD", display)
    key = "".join(ch for ch in key if unicodedata.category(ch) != "Mn")
    key = re.sub(r"\s+", " ", key).strip().casefold()
    if not any(ch.isalnum() for ch in key):
        raise ValueError("Nome do vendedor invalido.")
    return key


def clean_seller_name(name):
    display = re.sub(r"\s+", " ", str(name or "").strip())
    normalize_seller_name(display)
    return display
