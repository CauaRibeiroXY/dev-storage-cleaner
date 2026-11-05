import os
import sys
import argparse

# Configurar UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.cleaner import StorageCleaner, check_the_sims_guard

def print_banner():
    print("=" * 70)
    print("  DEV STORAGE CLEANER & CACHE PURGER - CLI SEGURO")
    print("=" * 70)
    guard = check_the_sims_guard()
    sims_status = "EM EXECUÇÃO" if guard['is_running'] else "NÃO EM EXECUÇÃO"
    print(f"[*] PROTEÇÃO ATIVA: {guard['process_name']} -> {sims_status}")
    print(f"[*] STATUS DE ISOLAMENTO: {guard['status']}")
    print("-" * 70)

def run_scan():
    print_banner()
    print("[*] Iniciando varredura analítica de arquivos temporários e caches...")
    data = StorageCleaner.scan_all()

    print("\nCategorias Mapeadas:")
    for c in data["categories"]:
        paths_preview = f"({len(c['paths'])} caminho(s))" if c['paths'] else "(vazio/inexistente)"
        print(f"  [{c['id']}] {c['name']}")
        print(f"      Tamanho: {c['formatted_size']} | {c['file_count']} arquivos {paths_preview}")

    print("\n" + "=" * 70)
    print(f"[+] TOTAL RECUPERÁVEL ESTIMADO: {data['total_reclaimable_formatted']} ({data['total_files']} arquivos)")
    print("=" * 70)
    print("Dica: Para executar a limpeza segura de fato, rode:")
    print("      python main.py --clean")

def run_clean(category=None):
    print_banner()
    if category:
        print(f"[*] Limpando categoria específica: '{category}'...")
        res = StorageCleaner.clean_category(category)
        if "error" in res:
            print(f"[-] Erro: {res['error']}")
            return
        print(f"[✓] Categoria '{category}' limpa com sucesso!")
        print(f"    Espaço liberado: {res['deleted_formatted']} ({res['deleted_files']} arquivos)")
    else:
        print("[*] Executando limpeza segura em todas as categorias permitidas...")
        res = StorageCleaner.clean_all()
        print("\nResultado por categoria:")
        for r in res["results"]:
            print(f"  - [{r['id']}]: {r.get('deleted_formatted', '0 B')} liberados ({r.get('deleted_files', 0)} arquivos)")

        print("\n" + "=" * 70)
        print(f"[✓] LIMPEZA CONCLUÍDA COM SUCESSO!")
        print(f"[+] ESPAÇO TOTAL LIBERADO NO DISCO: {res['total_deleted_formatted']}")
        print(f"[+] TOTAL DE ARQUIVOS PURGADOS: {res['total_files']}")
        print(f"[*] Processos de jogos (The Sims / EA) e repositórios continuam 100% preservados.")
        print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description="Limpador Seguro de Armazenamento para Desenvolvedores")
    parser.add_argument("--scan", action="store_true", help="Apenas escaneia sem deletar nada (Dry-Run)")
    parser.add_argument("--clean", action="store_true", help="Executa a limpeza segura de caches e temporários")
    parser.add_argument("--category", type=str, help="Limpa apenas uma categoria especifica (ex: npm_cache, pip_cache, matlab_temp, user_temp)")
    parser.add_argument("--web", action="store_true", help="Inicia o dashboard web")
    parser.add_argument("--port", type=int, default=5070, help="Porta do dashboard web (padrao: 5070)")

    args = parser.parse_args()

    if args.web:
        from web.app import run_web_app
        run_web_app(port=args.port)
    elif args.clean:
        run_clean(category=args.category)
    else:
        run_scan()

if __name__ == "__main__":
    main()
