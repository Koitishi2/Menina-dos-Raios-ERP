import json
import zipfile
from pathlib import Path


def backup_db_sources_from_paths(base_dir, db_path, company_dbs, app_notes_db_path):
    seen=set(); out=[]
    def add(key,label,path):
        p=Path(path)
        if p.exists() and p.is_file() and p.suffix.lower()==".db" and p.resolve() not in seen:
            seen.add(p.resolve()); out.append({"key":key,"label":label,"path":p})
    add("raios_monteiro","Menina dos Raios / Monteiro",db_path)
    for key,path in company_dbs.items():
        label={"raios":"Menina dos Raios / Monteiro","estrada":"Menina da Estrada"}.get(key,key)
        add(f"empresa_{key}",label,path)
    add("app_notes","Notas APP / Calendario",app_notes_db_path)
    for p in sorted(Path(base_dir).glob("*.db")):
        add(f"extra_{p.stem}",f"Banco extra: {p.name}",p)
    return out


def backup_expected_databases_from_paths(base_dir, db_path, company_dbs, app_notes_db_path):
    expected=[
        {"key":"raios_monteiro","label":"Menina dos Raios / Monteiro","path":db_path},
        {"key":"estrada","label":"Menina da Estrada","path":company_dbs.get("estrada",Path(base_dir)/"menina_estrada.db")},
        {"key":"app_notes","label":"Notas APP / Calendario","path":app_notes_db_path},
    ]
    return [
        {"key":item["key"],"label":item["label"],"name":Path(item["path"]).name,"exists":Path(item["path"]).exists()}
        for item in expected
    ]


def backup_files_from_dir(backup_dir):
    backup_dir=Path(backup_dir)
    return list(backup_dir.glob("bm_backup_*.db")) + list(backup_dir.glob("bm_backup_*.zip"))


def backup_manifest_databases_from_zip(path):
    try:
        with zipfile.ZipFile(path,"r") as zf:
            data=json.loads(zf.read("manifest.json").decode("utf-8"))
            return [d.get("filename") for d in data.get("databases",[]) if d.get("filename")]
    except Exception:
        return []
