import json
import shutil
import sqlite3
import tempfile
import zipfile
from pathlib import Path

from fastapi import HTTPException


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


def _valid_backup_name(filename:str)->bool:
    return filename.startswith("bm_backup_") and filename.lower().endswith((".db",".zip"))


def backup_path_for_filename(filename, backup_dir):
    if not _valid_backup_name(filename):
        raise HTTPException(400,"Arquivo invÃ¡lido.")
    base=Path(backup_dir).resolve()
    path=(base/filename).resolve()
    if not path.is_relative_to(base):
        raise HTTPException(400,"Arquivo invÃ¡lido.")
    return path


def backup_manifest_databases_from_zip(path):
    try:
        with zipfile.ZipFile(path,"r") as zf:
            data=json.loads(zf.read("manifest.json").decode("utf-8"))
            return [d.get("filename") for d in data.get("databases",[]) if d.get("filename")]
    except Exception:
        return []


def _copy_sqlite_consistent(src:Path,dest:Path):
    src_conn=sqlite3.connect(str(src),timeout=20)
    dest_conn=sqlite3.connect(str(dest),timeout=20)
    try:
        src_conn.backup(dest_conn)
    finally:
        dest_conn.close(); src_conn.close()


def _is_sqlite_file(path:Path)->bool:
    """Confere se o arquivo comeca com a assinatura magica do SQLite 3."""
    try:
        with open(path,"rb") as f:
            return f.read(16).startswith(b"SQLite format 3")
    except Exception:
        return False


def safety_backup_before_restore_with(create_backup_func)->str:
    """Cria backup de seguranca multi-banco antes de uma restauracao."""
    return create_backup_func("pre_restore")


def restore_zip_backup_with(src:Path, base_dir, db_path, app_notes_db_path, company_dbs):
    restored=[]
    allowed={p.name for p in [db_path, app_notes_db_path, *company_dbs.values()]}
    with tempfile.TemporaryDirectory() as td:
        tmpdir=Path(td)
        with zipfile.ZipFile(src,"r") as zf:
            members=[m for m in zf.namelist() if m.startswith("databases/") and m.lower().endswith(".db")]
            if not members:
                raise HTTPException(400,"Pacote de backup nÃ£o possui bancos de dados.")
            for m in members:
                name=Path(m).name
                if not name or name not in allowed:
                    continue
                out=tmpdir/name
                with zf.open(m) as rf, open(out,"wb") as wf:
                    wf.write(rf.read())
                if not _is_sqlite_file(out):
                    raise HTTPException(400,f"Banco invÃ¡lido dentro do backup: {name}")
                target=Path(base_dir)/name
                shutil.copy2(str(out),str(target))
                restored.append(name)
    if not restored:
        raise HTTPException(400,"Nenhum banco reconhecido foi restaurado.")
    return restored
