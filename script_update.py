# script_update.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 IPTV System - Atualização Automática
Autor: Josiel Jefferson
Versão: 3.0 (corrigida e otimizada)
"""

import requests
import os
import sys
import json
from datetime import datetime

# Importar processador
import m3u_processor

# ================= CONFIG =================

REPO_OWNER = "jeffersondplay"
REPO_NAME = "jeffersondplay"
BRANCH = "main"

API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/"
RAW_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}"

PASTA = "downloads"
OUTPUT = "docs"

os.makedirs(PASTA, exist_ok=True)
os.makedirs(OUTPUT, exist_ok=True)

IGNORAR = [
    "requirements.txt", ".gitignore", "README.md",
    "render.yaml", ".github", "docs", "api",
    ".gitkeep", "script_update.py", "m3u_processor.py"
]

HEADERS = {
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'IPTV-Bot'
}

# ================= FUNÇÕES =================

def listar_arquivos():
    print(f"📡 Buscando arquivos no GitHub...")
    try:
        r = requests.get(API_URL, headers=HEADERS, timeout=30)

        if r.status_code != 200:
            print("⚠️ API falhou, usando fallback...")
            return listar_arquivos_alternativo()

        itens = r.json()
        arquivos = []

        for item in itens:
            if item.get("type") != "file":
                continue

            nome = item["name"]

            if nome in IGNORAR:
                continue

            if nome.endswith((".m3u", ".m3u8", ".txt")):
                arquivos.append({
                    "name": nome,
                    "url": item["download_url"],
                    "size": item.get("size", 0),
                    "local": False
                })
                print(f"  📄 {nome}")

        if not arquivos:
            print("⚠️ Nenhuma playlist encontrada, usando fallback...")
            return listar_arquivos_alternativo()

        return arquivos

    except Exception as e:
        print(f"❌ Erro: {e}")
        return listar_arquivos_alternativo()


def listar_arquivos_alternativo():
    print("🔄 Método alternativo...")
    nomes = [
        "playlists.m3u", "playlist.m3u",
        "canais.m3u", "lista.m3u"
    ]

    arquivos = []

    for nome in nomes:
        url = f"{RAW_URL}/{nome}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                arquivos.append({
                    "name": nome,
                    "url": url,
                    "size": len(r.content),
                    "local": False
                })
                print(f"  ✅ {nome}")
        except:
            pass

    return arquivos


def criar_exemplo_playlist():
    print("📝 Criando playlist de exemplo...")

    caminho = os.path.join(PASTA, "exemplo.m3u")

    conteudo = """#EXTM3U
#EXTINF:-1 group-title="Teste",Canal Teste
http://example.com/stream
"""

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)

    return [{
        "name": "exemplo.m3u",
        "url": caminho,
        "size": len(conteudo),
        "local": True
    }]


def baixar_arquivos(arquivos):
    print(f"\n⬇️ Baixando {len(arquivos)} arquivo(s)...")

    for arq in arquivos:
        nome = arq["name"]
        url = arq["url"]
        caminho = os.path.join(PASTA, nome)

        try:
            # 🔥 CORREÇÃO PRINCIPAL
            if arq.get("local") or not url.startswith("http"):
                print(f"  📁 {nome} já local ✅")
                continue

            print(f"  📥 {nome}...", end=" ")

            r = requests.get(url, timeout=30)
            r.raise_for_status()

            with open(caminho, "wb") as f:
                f.write(r.content)

            print("✅")

        except Exception as e:
            print(f"❌ {e}")
            return False

    return True


def adicionar_timestamp(arquivo, total):
    try:
        with open(arquivo, "a", encoding="utf-8") as f:
            f.write(f"\n\n# Atualizado em {datetime.now()}\n")
            f.write(f"# Total canais: {total}\n")
        return True
    except:
        return False


def gerar_metadata(canais, stats):
    data = {
        "generated_at": datetime.now().isoformat(),
        "total_channels": len(canais),
        "stats": stats
    }

    with open(os.path.join(OUTPUT, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def limpar():
    print("🧹 Limpando downloads...")
    for f in os.listdir(PASTA):
        if f != ".gitkeep":
            try:
                os.remove(os.path.join(PASTA, f))
            except:
                pass


# ================= MAIN =================

def main():
    print("=" * 50)
    print("🚀 IPTV AUTO UPDATE v3.0")
    print("=" * 50)

    arquivos = listar_arquivos()

    if not arquivos:
        arquivos = criar_exemplo_playlist()

    if not baixar_arquivos(arquivos):
        sys.exit(1)

    arquivos_baixados = [
        f for f in os.listdir(PASTA)
        if f.endswith((".m3u", ".txt"))
    ]

    if not arquivos_baixados:
        print("❌ Nenhuma playlist válida")
        sys.exit(1)

    print("\n📝 Processando...")
    canais, stats = m3u_processor.processar_lista(PASTA, OUTPUT)

    playlist_saida = os.path.join(OUTPUT, "playlists.m3u")

    adicionar_timestamp(playlist_saida, stats["canais_unicos"])
    gerar_metadata(canais, stats)

    print("\n📊 Resultado:")
    print(f"  • Canais: {stats['canais_unicos']}")
    print(f"  • Arquivos: {stats['arquivos_processados']}")

    limpar()

    print("\n✅ Finalizado com sucesso!")


if __name__ == "__main__":
    main()
