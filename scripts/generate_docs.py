import os
import sys
import pydoc
import subprocess

OUTPUT_DIR = "../wiki"  # Diretório onde os arquivos Markdown serão gerados
EXCLUDED_DIRS = [
    "venv",
    ".git",
    "__pycache__",
    "site-packages",
]  # Diretórios a serem ignorados
GITHUB_WIKI_URL = "https://github.com/BuBitt/ufcg-sigaa-scraper.wiki.git"  # Substitua pelo URL correto do Wiki


def generate_docs():
    """
    Gera a documentação em formato Markdown para todos os módulos do projeto.

    Este método percorre os diretórios do projeto, identifica arquivos Python
    e gera documentação baseada nas docstrings de cada módulo. Os arquivos
    gerados são salvos no diretório especificado em OUTPUT_DIR.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Adicionar o diretório raiz do projeto ao sys.path para garantir que os módulos sejam encontrados
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, project_root)

    for root, dirs, files in os.walk(project_root):
        # Ignorar diretórios excluídos
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                module_path = (
                    os.path.relpath(os.path.join(root, file), project_root)
                    .replace(os.sep, ".")
                    .replace(".py", "")
                )
                # Ignorar módulos que não pertencem ao projeto
                if not module_path.startswith("ufcg-sigaa-scraper"):
                    continue

                output_file = os.path.join(OUTPUT_DIR, f"{module_path}.md")
                try:
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(f"# Documentação do módulo `{module_path}`\n\n")
                        f.write(pydoc.render_doc(module_path, renderer=pydoc.plaintext))
                except ImportError as e:
                    print(f"Erro ao gerar documentação para {module_path}: {e}")
                except Exception as e:
                    print(f"Erro inesperado ao processar {module_path}: {e}")


def is_git_repo(directory):
    """
    Verifica se o diretório especificado é um repositório Git válido.

    Args:
        directory (str): Caminho do diretório a ser verificado.

    Returns:
        bool: Retorna True se o diretório for um repositório Git válido, caso contrário False.
    """
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=directory,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def initialize_git_repo(directory):
    """
    Inicializa um repositório Git no diretório especificado, se necessário.

    Args:
        directory (str): Caminho do diretório onde o repositório Git será inicializado.
    """
    try:
        if not is_git_repo(directory):
            subprocess.run(["git", "init"], cwd=directory, check=True)
            subprocess.run(
                ["git", "remote", "add", "origin", GITHUB_WIKI_URL],
                cwd=directory,
                check=True,
            )
            print(f"Repositório Git inicializado e vinculado ao Wiki em {directory}.")
        else:
            # Verificar se o remoto 'origin' existe
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            if result.returncode != 0:  # O remoto 'origin' não existe
                subprocess.run(
                    ["git", "remote", "add", "origin", GITHUB_WIKI_URL],
                    cwd=directory,
                    check=True,
                )
                print(f"Remoto 'origin' adicionado ao repositório em {directory}.")
            elif (
                GITHUB_WIKI_URL not in result.stdout
            ):  # O remoto 'origin' está incorreto
                subprocess.run(
                    ["git", "remote", "set-url", "origin", GITHUB_WIKI_URL],
                    cwd=directory,
                    check=True,
                )
                print(f"URL do remoto 'origin' atualizado para {GITHUB_WIKI_URL}.")
    except Exception as e:
        print(f"Erro ao inicializar ou configurar o repositório Git: {e}")


def sync_with_remote(directory):
    """
    Sincroniza o repositório local com o remoto.

    Args:
        directory (str): Caminho do diretório do repositório Git.
    """
    try:
        subprocess.run(["git", "fetch", "origin"], cwd=directory, check=True)
        subprocess.run(
            ["git", "reset", "--hard", "origin/master"], cwd=directory, check=True
        )
        print(f"Repositório sincronizado com o remoto em {directory}.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao sincronizar com o repositório remoto: {e}")


def push_to_github_wiki():
    """
    Faz commit e push dos arquivos gerados para o repositório do GitHub Wiki.

    Este método verifica se o diretório OUTPUT_DIR é um repositório Git válido,
    inicializa o repositório se necessário, sincroniza com o remoto e então
    realiza o commit e push dos arquivos gerados.
    """
    initialize_git_repo(OUTPUT_DIR)
    sync_with_remote(OUTPUT_DIR)

    try:
        # Verificar se há mudanças antes de tentar o commit
        subprocess.run(["git", "add", "."], cwd=OUTPUT_DIR, check=True)
        result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=OUTPUT_DIR)
        if result.returncode != 0:  # Há mudanças para commit
            subprocess.run(
                ["git", "commit", "-m", "Atualiza documentação gerada automaticamente"],
                cwd=OUTPUT_DIR,
                check=True,
            )
            subprocess.run(
                ["git", "push", "-u", "origin", "master"], cwd=OUTPUT_DIR, check=True
            )
            print("Documentação publicada no GitHub Wiki com sucesso!")
        else:
            print("Nenhuma mudança detectada. Nada para publicar.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao publicar no GitHub Wiki: {e}")


if __name__ == "__main__":
    generate_docs()
    push_to_github_wiki()
