#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de atualização automática IPTV
Autor: Josiel Jefferson
Versão: 2.2
"""

import requests
import os
import sys
import json
import shutil
from datetime import datetime

# Importar o processador
import m3u_processor

# Configurações
API_URL = "https://api.github.com/repos/jeffersondplay/jeffersondplay/contents/"
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
    ".github",
    "docs",
    "api",
    ".gitkeep"
]

def listar_arquivos():
    """Lista arquivos disponíveis no repositório"""
    try:
        print("📡 Buscando arquivos no GitHub...")
        
        # Tentar diferentes URLs possíveis
        urls_teste = [
            "https://api.github.com/repos/jeffersondplay/jeffersondplay/contents/",
            "https://api.github.com/repos/jeffersondplay/jeffersondplay/contents/downloads",
            "https://raw.githubusercontent.com/jeffersondplay/jeffersondplay/main/"
        ]
        
        arquivos = []
        
        for url_teste in urls_teste:
            try:
                r = requests.get(url_teste, timeout=30)
                if r.status_code == 200:
                    print(f"  ✅ Conectado a: {url_teste}")
                    break
            except:
                continue
        
        r.raise_for_status()
        
        items = r.json()
        
        # Se for uma lista, processar normalmente
        if isinstance(items, list):
            for item in items:
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
        else:
            print("  ⚠️ Resposta inesperada da API")
        
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

def adicionar_timestamp(m3u_file, total_canais):
    """Adiciona timestamp ao final do arquivo M3U"""
    try:
        timestamp = datetime.now().strftime('%d/%m/%Y - %H:%M:%S')
        with open(m3u_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n# Atualizado em {timestamp} BRT\n")
            f.write(f"# Total de canais: {total_canais}\n")
            f.write(f"# Fonte: GitHub Actions - jeffersondplay\n")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao adicionar timestamp: {e}")
        return False

def gerar_metadata(canais, stats):
    """Gera arquivo de metadados"""
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "generated_at_br": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        "version": "2.2",
        "author": "Jefferson Dplay",
        "repo": "jeffersondplay/jeffersondplay",
        "stats": stats,
        "total_channels": len(canais),
        "epg_sources": len(m3u_processor.EPG_URLS),
        "epg_urls": m3u_processor.EPG_URLS,
        "server_info": {
            "name": "IPTV System",
            "url": "https://jeffersondplay.onrender.com",
            "username": "josielluz"
        }
    }
    
    with open(os.path.join(OUTPUT, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def limpar_pasta_downloads():
    """Limpa apenas os arquivos baixados, mantendo a estrutura"""
    try:
        for arquivo in os.listdir(PASTA):
            caminho = os.path.join(PASTA, arquivo)
            # Não remover o .gitkeep
            if arquivo != ".gitkeep" and os.path.isfile(caminho):
                os.remove(caminho)
                print(f"  🗑️ Removido: {arquivo}")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao limpar pasta: {e}")
        return False

def main():
    """Função principal"""
    print("=" * 50)
    print("🚀 IPTV System - Atualização Automática")
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"👤 Repositório: jeffersondplay/jeffersondplay")
    print("=" * 50)
    
    # Listar e baixar arquivos
    arquivos = listar_arquivos()
    if not baixar_arquivos(arquivos):
        print("❌ Falha no download dos arquivos")
        sys.exit(1)
    
    # Verificar se há arquivos para processar
    arquivos_baixados = [f for f in os.listdir(PASTA) if f.endswith(('.m3u', '.m3u8', '.txt'))]
    if not arquivos_baixados:
        print("⚠️ Nenhum arquivo de playlist encontrado para processar")
        sys.exit(0)
    
    # Processar playlists
    print("\n📝 Processando playlists...")
    try:
        canais, stats = m3u_processor.processar_lista(PASTA, OUTPUT)
        
        print(f"\n📊 Estatísticas:")
        print(f"  • Arquivos processados: {stats['arquivos_processados']}")
        print(f"  • Canais únicos: {stats['canais_unicos']}")
        print(f"  • Erros: {stats['erros']}")
        
        # Mostrar detalhes por arquivo
        if "arquivos" in stats:
            print(f"\n  📁 Detalhes por arquivo:")
            for arquivo in stats["arquivos"]:
                print(f"    • {arquivo['nome']}: {arquivo['canais']} canais")
        
        # Adicionar timestamp
        m3u_file = os.path.join(OUTPUT, "playlists.m3u")
        adicionar_timestamp(m3u_file, stats['canais_unicos'])
        
        # Gerar metadados
        gerar_metadata(canais, stats)
        
        print(f"\n✅ Atualização concluída com sucesso!")
        print(f"📁 Playlist salva em: {m3u_file}")
        print(f"📊 JSON salvo em: {OUTPUT}/channels.json")
        print(f"📈 Estatísticas em: {OUTPUT}/stats.json")
        
    except Exception as e:
        print(f"❌ Erro no processamento: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Limpar arquivos temporários
    print("\n🧹 Limpando arquivos temporários...")
    limpar_pasta_downloads()
    
    print("✅ Limpeza concluída")
    print("=" * 50)
    print("🎉 Sistema atualizado com sucesso!")

if __name__ == "__main__":
    main()