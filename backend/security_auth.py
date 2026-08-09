import time as _time_mod


_LOGIN_ATTEMPTS: dict = {}     # ip -> [(timestamp_unix, success_bool), ...]
LOGIN_RATE_WINDOW = 60          # janela onde contamos falhas
LOGIN_RATE_MAX_FAILS = 10       # max falhas na janela antes de bloquear
LOGIN_RATE_BLOCK_SECS = 300     # tempo de bloqueio apos estourar (5min)


def _check_login_rate(ip: str):
    """Retorna (permitido: bool, segundos_para_desbloqueio: int)."""
    now = _time_mod.time()
    history = _LOGIN_ATTEMPTS.get(ip, [])
    # Mantem so entradas dentro da janela de bloqueio
    history = [(t,s) for (t,s) in history if now - t < LOGIN_RATE_BLOCK_SECS]
    _LOGIN_ATTEMPTS[ip] = history
    # Conta falhas recentes (na janela curta de deteccao)
    recent_fails = [t for (t,s) in history if not s and now - t < LOGIN_RATE_WINDOW]
    if len(recent_fails) >= LOGIN_RATE_MAX_FAILS:
        oldest_fail = min(recent_fails)
        retry = int(LOGIN_RATE_BLOCK_SECS - (now - oldest_fail))
        return (False, max(retry, 1))
    return (True, 0)


def _record_login(ip: str, success: bool):
    """Registra tentativa. Em sucesso, limpa historico do IP."""
    if success:
        _LOGIN_ATTEMPTS.pop(ip, None); return
    _LOGIN_ATTEMPTS.setdefault(ip, []).append((_time_mod.time(), False))
    # Protecao: limpa dict se crescer demais (ataque tentando OOM)
    if len(_LOGIN_ATTEMPTS) > 10000:
        now = _time_mod.time()
        for k in list(_LOGIN_ATTEMPTS.keys()):
            _LOGIN_ATTEMPTS[k] = [(t,s) for (t,s) in _LOGIN_ATTEMPTS[k] if now - t < LOGIN_RATE_BLOCK_SECS]
            if not _LOGIN_ATTEMPTS[k]: del _LOGIN_ATTEMPTS[k]
