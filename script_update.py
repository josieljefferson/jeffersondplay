#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de atualização automática IPTV
Autor: Josiel Jefferson
Versão: 2.0
"""

import requests
import os
import sys
import json
from datetime import datetime
from m3u_processor import processar_lista

# Configurações
API_URL = "https://api.github.com/repos/josieljefferson/jeffersondplay/contents/"
PASTA = "downloads"
OUTPUT = "docs"

# Criar pastas se não existirem
os.makedirs(PASTA, exist_ok=True)
os.makedirs(OUTPUT, exist_ok=True)

# Arquivos a serem ignorados
IGNORAR = [
    "requirements.txt", 
    ".gitignore", 
    "README.md",
    "render.yaml",
    ".github"
]

def listar_arquivos():
    """Lista arquivos disponíveis no repositório"""
    try:
        print("📡 Buscando arquivos no GitHub...")
        r = requests.get(API_URL, timeout=30)
        r.raise_for_status()
        
        arquivos = []
        for item in r.json():
            nome = item["name"]
            
            # Ignorar arquivos específicos
            if nome in IGNORAR:
                continue
            
            # Aceitar listas IPTV
            if nome.endswith((".m3u", ".m3u8", ".txt")):
                arquivos.append({
                    "name": nome,
                    "url": item["download_url"],
                    "size": item.get("size", 0)
                })
                print(f"  📄 Encontrado: {nome} ({item.get('size', 0)} bytes)")
        
        return arquivos
    except Exception as e:
        print(f"❌ Erro ao listar arquivos: {e}")
        return []

def baixar_arquivos(arquivos):
    """Baixa os arquivos do GitHub"""
    if not arquivos:
        print("⚠️ Nenhum arquivo encontrado para baixar")
        return False
    
    print(f"\n⬇️ Baixando {len(arquivos)} arquivo(s)...")
    
    for arquivo in arquivos:
        nome = arquivo["name"]
        url = arquivo["url"]
        caminho = os.path.join(PASTA, nome)
        
        try:
            print(f"  📥 {nome}...", end=" ")
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            
            with open(caminho, "wb") as f:
                f.write(r.content)
            
            print("✅")
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
    
    return True

def adicionar_timestamp(m3u_file):
    """Adiciona timestamp ao final do arquivo M3U"""
    try:
        timestamp = datetime.now().strftime('%d/%m/%Y - %H:%M:%S')
        with open(m3u_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n# Atualizado em {timestamp} BRT\n")
            f.write(f"# Total de canais: {len(open(m3u_file).readlines())}\n")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao adicionar timestamp: {e}")
        return False

def gerar_metadata(canais, stats):
    """Gera arquivo de metadados"""
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "generated_at_br": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        "version": "2.0",
        "author": "Josiel Jefferson",
        "stats": stats,
        "total_channels": len(canais),
        "epg_sources": len(m3u_processor.EPG_URLS),
        "server_info": {
            "name": "IPTV System",
            "url": "https://jeffersondplay.onrender.com",
            "username": "josielluz"
        }
    }
    
    with open(os.path.join(OUTPUT, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def main():
    """Função principal"""
    print("=" * 50)
    print("🚀 IPTV System - Atualização Automática")
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 50)
    
    # Listar e baixar arquivos
    arquivos = listar_arquivos()
    if not baixar_arquivos(arquivos):
        print("❌ Falha no download dos arquivos")
        sys.exit(1)
    
    # Processar playlists
    print("\n📝 Processando playlists...")
    try:
        from m3u_processor import EPG_URLS as epg_urls
        canais, stats = processar_lista(PASTA, OUTPUT)
        
        print(f"\n📊 Estatísticas:")
        print(f"  • Arquivos processados: {stats['arquivos_processados']}")
        print(f"  • Canais únicos: {stats['canais_unicos']}")
        print(f"  • Erros: {stats['erros']}")
        
        # Adicionar timestamp
        m3u_file = os.path.join(OUTPUT, "playlists.m3u")
        adicionar_timestamp(m3u_file)
        
        # Gerar metadados
        gerar_metadata(canais, stats)
        
        print(f"\n✅ Atualização concluída com sucesso!")
        print(f"📁 Playlist salva em: {m3u_file}")
        print(f"📊 JSON salvo em: {OUTPUT}/channels.json")
        
    except Exception as e:
        print(f"❌ Erro no processamento: {e}")
        sys.exit(1)
    
    # Limpar arquivos temporários
    print("\n🧹 Limpando arquivos temporários...")
    for arquivo in os.listdir(PASTA):
        caminho = os.path.join(PASTA, arquivo)
        if os.path.isfile(caminho):
            os.remove(caminho)
    
    print("✅ Limpeza concluída")
    print("=" * 50)

if __name__ == "__main__":
    main()