import json


TAB_PERMISSION_ALIASES = {
    "notas": ["notas", "pendentes"],
    "pendentes": ["pendentes", "notas"],
}


def _expand_tab_keys(keys:list)->list:
    out = []
    for key in keys or []:
        for item in TAB_PERMISSION_ALIASES.get(key, [key]):
            if item not in out:
                out.append(item)
    return out


def tab_permissions_map_from_db(get_control_db_func)->dict:
    conn=get_control_db_func()
    try:
        row=conn.execute("SELECT value FROM settings WHERE key='tab_permissions'").fetchone()
        perms=json.loads(row["value"]) if row and row["value"] else {}
        return perms if isinstance(perms,dict) else {}
    except Exception:
        return {}
    finally:
        conn.close()


def permissions_configured_from_map(perms:dict)->bool:
    return any(bool(v) for v in perms.values())


def session_has_any_tab_from_map(sess:dict, keys:list, perms:dict)->bool:
    if sess.get("role")=="admin":
        return True
    allowed=perms.get(sess.get("role",""),[]) if isinstance(perms,dict) else []
    return any(k in allowed for k in _expand_tab_keys(keys))
