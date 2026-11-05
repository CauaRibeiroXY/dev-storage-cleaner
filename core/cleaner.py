import os
import sys
import shutil
import glob
from typing import Dict, List, Any

# Suporte UTF-8 no terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PROTECTED_PROCESS_KEYWORDS = ["TS4", "The Sims", "Electronic Arts", "EA Games", "Origin", "Link2EA"]
PROTECTED_PATH_KEYWORDS = ["The Sims", "Electronic Arts", "Mods", "Saves", "financeiroCS", ".git"]

def format_bytes(bytes_num: int) -> str:
    """Formata bytes em KB, MB ou GB de forma legivel"""
    if bytes_num < 1024:
        return f"{bytes_num} B"
    elif bytes_num < 1024 * 1024:
        return f"{bytes_num / 1024:.2f} KB"
    elif bytes_num < 1024 * 1024 * 1024:
        return f"{bytes_num / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_num / (1024 * 1024 * 1024):.2f} GB"

def is_path_protected(path: str) -> bool:
    """Verifica se o caminho contem qualquer palavra protegida"""
    p_lower = path.lower()
    for kw in PROTECTED_PATH_KEYWORDS:
        if kw.lower() in p_lower:
            return True
    return False

def check_the_sims_guard() -> Dict[str, Any]:
    """
    Verifica o estado do The Sims para certificar ao usuario que ele esta protegido e intocado.
    """
    is_running = False
    try:
        import subprocess
        out = subprocess.check_output('tasklist /FI "IMAGENAME eq TS4_x64.exe" /NH', shell=True, text=True, errors='ignore')
        if "TS4_x64" in out:
            is_running = True
    except Exception:
        pass

    return {
        "protected": True,
        "process_name": "TS4_x64.exe (The Sims 4)",
        "is_running": is_running,
        "status": "IMUNE & PROTEGIDO (Nenhum arquivo ou processo sera tocado)"
    }

class StorageCleaner:
    """
    Motor seguro de varredura e limpeza de caches e arquivos temporarios de desenvolvimento.
    """

    @classmethod
    def get_categories(cls) -> Dict[str, Dict[str, Any]]:
        categories = {}
        local_app = os.getenv("LOCALAPPDATA", "")
        temp_dir = os.getenv("TEMP", "")

        # 1. Cache do NPM
        npm_dir = os.path.join(local_app, "npm-cache")
        categories["npm_cache"] = {
            "name": "Cache do NPM / Node.js",
            "description": "Pacotes e tarballs baixados pelo npm/npx",
            "paths": [npm_dir] if os.path.exists(npm_dir) else []
        }

        # 2. Cache do PIP
        pip_dir = os.path.join(local_app, "pip", "cache")
        categories["pip_cache"] = {
            "name": "Cache de Pacotes Python (Pip)",
            "description": "Wheels e downloads em cache do pip",
            "paths": [pip_dir] if os.path.exists(pip_dir) else []
        }

        # 3. Crash Dumps do Windows
        dumps_dir = os.path.join(local_app, "CrashDumps")
        categories["crash_dumps"] = {
            "name": "Windows User Crash Dumps",
            "description": "Relatórios e dumps de memória de falhas passadas",
            "paths": [dumps_dir] if os.path.exists(dumps_dir) else []
        }

        # 4. Pasta Temporária de Usuário (%TEMP%)
        categories["user_temp"] = {
            "name": "Arquivos Temporários de Usuário (%TEMP%)",
            "description": "Arquivos .tmp, logs e caches de programas fechados",
            "paths": [temp_dir] if os.path.exists(temp_dir) else []
        }

        # 5. Instaladores Descompactados de Teste no Downloads
        downloads_dir = r"F:\Users\Kaka\Downloads"
        temp_matlabs = glob.glob(os.path.join(downloads_dir, "_temp_matlab_*"))
        categories["matlab_temp"] = {
            "name": "Pastas Temporárias de Instaladores (Downloads)",
            "description": "Resíduos temporários de descompactação de instaladores antigos",
            "paths": temp_matlabs
        }

        return categories

    @classmethod
    def scan_category(cls, cat_id: str, info: Dict[str, Any]) -> Dict[str, Any]:
        total_size = 0
        file_count = 0
        items_found = []

        for p in info.get("paths", []):
            if not os.path.exists(p) or is_path_protected(p):
                continue

            if os.path.isfile(p):
                try:
                    sz = os.path.getsize(p)
                    total_size += sz
                    file_count += 1
                except Exception:
                    pass
            elif os.path.isdir(p):
                # Se for user_temp, varremos apenas arquivos nao bloqueados
                for root, dirs, files in os.walk(p):
                    # Proteger se algum subdiretorio bater com regra
                    if is_path_protected(root):
                        continue
                    for f in files:
                        fp = os.path.join(root, f)
                        if is_path_protected(fp):
                            continue
                        try:
                            sz = os.path.getsize(fp)
                            total_size += sz
                            file_count += 1
                        except Exception:
                            pass

        return {
            "id": cat_id,
            "name": info["name"],
            "description": info["description"],
            "paths": info["paths"],
            "total_bytes": total_size,
            "formatted_size": format_bytes(total_size),
            "file_count": file_count
        }

    @classmethod
    def scan_all(cls) -> Dict[str, Any]:
        categories = cls.get_categories()
        results = []
        total_bytes = 0
        total_files = 0

        for cat_id, info in categories.items():
            scanned = cls.scan_category(cat_id, info)
            results.append(scanned)
            total_bytes += scanned["total_bytes"]
            total_files += scanned["file_count"]

        return {
            "sims_guard": check_the_sims_guard(),
            "categories": results,
            "total_reclaimable_bytes": total_bytes,
            "total_reclaimable_formatted": format_bytes(total_bytes),
            "total_files": total_files
        }

    @classmethod
    def clean_category(cls, cat_id: str) -> Dict[str, Any]:
        """Limpa de forma segura uma categoria selecionada"""
        categories = cls.get_categories()
        if cat_id not in categories:
            return {"error": f"Categoria '{cat_id}' nao encontrada."}

        info = categories[cat_id]
        deleted_bytes = 0
        deleted_files = 0
        errors = 0

        for p in info.get("paths", []):
            if not os.path.exists(p) or is_path_protected(p):
                continue

            # Para pastas completas que sao 100% de cache ou temporarias (ex: _temp_matlab_* ou CrashDumps)
            if cat_id in ["matlab_temp", "crash_dumps"]:
                if os.path.isdir(p):
                    try:
                        # Calcular tamanho antes de apagar
                        for root, _, files in os.walk(p):
                            for f in files:
                                fp = os.path.join(root, f)
                                try:
                                    deleted_bytes += os.path.getsize(fp)
                                    deleted_files += 1
                                except Exception:
                                    pass
                        shutil.rmtree(p, ignore_errors=True)
                    except Exception:
                        errors += 1

            elif cat_id in ["npm_cache", "pip_cache"]:
                # Limpar conteudo interno da pasta de cache
                if os.path.isdir(p):
                    for item in os.listdir(p):
                        item_path = os.path.join(p, item)
                        if is_path_protected(item_path):
                            continue
                        try:
                            if os.path.isfile(item_path) or os.path.islink(item_path):
                                deleted_bytes += os.path.getsize(item_path)
                                os.remove(item_path)
                                deleted_files += 1
                            elif os.path.isdir(item_path):
                                for root, _, files in os.walk(item_path):
                                    for f in files:
                                        fp = os.path.join(root, f)
                                        try:
                                            deleted_bytes += os.path.getsize(fp)
                                            deleted_files += 1
                                        except Exception:
                                            pass
                                shutil.rmtree(item_path, ignore_errors=True)
                        except Exception:
                            errors += 1

            elif cat_id == "user_temp":
                # No %TEMP%, apagamos arquivos seguros e ignoramos arquivos travados pelo SO
                if os.path.isdir(p):
                    for item in os.listdir(p):
                        item_path = os.path.join(p, item)
                        if is_path_protected(item_path):
                            continue
                        try:
                            if os.path.isfile(item_path) or os.path.islink(item_path):
                                sz = os.path.getsize(item_path)
                                os.remove(item_path)
                                deleted_bytes += sz
                                deleted_files += 1
                            elif os.path.isdir(item_path):
                                sub_bytes = 0
                                sub_files = 0
                                for root, _, files in os.walk(item_path):
                                    for f in files:
                                        fp = os.path.join(root, f)
                                        try:
                                            sub_bytes += os.path.getsize(fp)
                                            sub_files += 1
                                        except Exception:
                                            pass
                                shutil.rmtree(item_path, ignore_errors=True)
                                if not os.path.exists(item_path):
                                    deleted_bytes += sub_bytes
                                    deleted_files += sub_files
                        except Exception:
                            errors += 1

        return {
            "id": cat_id,
            "status": "success",
            "deleted_bytes": deleted_bytes,
            "deleted_formatted": format_bytes(deleted_bytes),
            "deleted_files": deleted_files,
            "skipped_or_locked": errors
        }

    @classmethod
    def clean_all(cls) -> Dict[str, Any]:
        categories = cls.get_categories()
        results = []
        total_deleted = 0
        total_files = 0

        for cat_id in categories.keys():
            res = cls.clean_category(cat_id)
            results.append(res)
            total_deleted += res.get("deleted_bytes", 0)
            total_files += res.get("deleted_files", 0)

        return {
            "sims_guard": check_the_sims_guard(),
            "results": results,
            "total_deleted_bytes": total_deleted,
            "total_deleted_formatted": format_bytes(total_deleted),
            "total_files": total_files
        }
