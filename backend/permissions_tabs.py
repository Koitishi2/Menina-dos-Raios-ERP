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
