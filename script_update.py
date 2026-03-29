#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de atualização automática IPTV
Autor: Josiel Jefferson
Versão: 2.3
"""

import requests
import os
import sys
import json
from datetime import datetime

# Importar o processador
import m3u_processor

# Configurações - CORRIGIDO
REPO_OWNER = "jeffersondplay"
REPO_NAME = "jeffersondplay"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/"
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
    ".gitkeep",
    "script_update.py",
    "m3u_processor.py"
]

def listar_arquivos():
    """Lista arquivos disponíveis no repositório"""
    try:
        print(f"📡 Buscando arquivos em: {API_URL}")
        
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'IPTV-Bot'
        }
        
        response = requests.get(API_URL, headers=headers, timeout=30)
        
        if response.status_code == 404:
            print(f"  ⚠️ Repositório não encontrado ou privado")
            print(f"  🔧 Tentando método alternativo...")
            return listar_arquivos_alternativo()
        
        response.raise_for_status()
        
        items = response.json()
        arquivos = []
        
        # Se for uma lista, processar normalmente
        if isinstance(items, list):
            for item in items:
                nome = item["name"]
                tipo = item.get("type", "file")
                
                # Pular diretórios
                if tipo == "dir":
                    continue
                
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
            
            if not arquivos:
                print("  ⚠️ Nenhum arquivo .m3u encontrado no diretório raiz")
                print("  🔧 Tentando buscar na pasta downloads...")
                return listar_arquivos_downloads()
        else:
            print("  ⚠️ Resposta inesperada da API")
        
        return arquivos
        
    except Exception as e:
        print(f"❌ Erro ao listar arquivos: {e}")
        return listar_arquivos_alternativo()

def listar_arquivos_downloads():
    """Tenta listar arquivos da pasta downloads"""
    try:
        url_downloads = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/downloads"
        print(f"📡 Buscando em: {url_downloads}")
        
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'IPTV-Bot'
        }
        
        response = requests.get(url_downloads, headers=headers, timeout=30)
        
        if response.status_code == 200:
            items = response.json()
            arquivos = []
            
            if isinstance(items, list):
                for item in items:
                    nome = item["name"]
                    
                    if nome.endswith((".m3u", ".m3u8", ".txt")):
                        arquivos.append({
                            "name": nome,
                            "url": item["download_url"],
                            "size": item.get("size", 0)
                        })
                        print(f"  📄 Encontrado em /downloads: {nome} ({item.get('size', 0)} bytes)")
                
                return arquivos
        
        return []
        
    except Exception as e:
        print(f"⚠️ Erro ao buscar pasta downloads: {e}")
        return []

def listar_arquivos_alternativo():
    """Método alternativo: busca direto no raw.githubusercontent"""
    try:
        print("  🔄 Tentando método alternativo...")
        
        # Lista de possíveis arquivos
        possiveis_arquivos = [
            "playlists.m3u",
            "playlist.m3u", 
            "canais.m3u",
            "lista.m3u",
            "playlists-official.m3u",
            "playlists-oficial.m3u"
        ]
        
        arquivos = []
        
        for nome_arquivo in possiveis_arquivos:
            url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{nome_arquivo}"
            
            try:
                print(f"  🔍 Testando: {nome_arquivo}...", end=" ")
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    # Salvar arquivo temporariamente
                    caminho = os.path.join(PASTA, nome_arquivo)
                    with open(caminho, "wb") as f:
                        f.write(response.content)
                    
                    print("✅ Encontrado!")
                    arquivos.append({
                        "name": nome_arquivo,
                        "url": url,
                        "size": len(response.content)
                    })
                else:
                    print("❌")
                    
            except Exception as e:
                print(f"❌ Erro: {e}")
        
        return arquivos
        
    except Exception as e:
        print(f"❌ Erro no método alternativo: {e}")
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
            
            # Verificar se o arquivo não está vazio
            if os.path.getsize(caminho) > 0:
                print("✅")
            else:
                print("⚠️ Arquivo vazio, ignorando")
                os.remove(caminho)
                
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
            f.write(f"# Fonte: GitHub Actions - {REPO_OWNER}\n")
        return True
    except Exception as e:
        print(f"⚠️ Erro ao adicionar timestamp: {e}")
        return False

def gerar_metadata(canais, stats):
    """Gera arquivo de metadados"""
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "generated_at_br": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        "version": "2.3",
        "author": "Jefferson Dplay",
        "repo": f"{REPO_OWNER}/{REPO_NAME}",
        "stats": stats,
        "total_channels": len(canais),
        "epg_sources": len(m3u_processor.EPG_URLS),
        "epg_urls": m3u_processor.EPG_URLS[:5],  # Limitar a 5 para não ficar muito grande
        "server_info": {
            "name": "IPTV System",
            "url": f"https://{REPO_OWNER}.onrender.com",
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

def criar_exemplo_playlist():
    """Cria uma playlist de exemplo se nenhuma for encontrada"""
    exemplo_path = os.path.join(PASTA, "exemplo.m3u")
    
    conteudo = """#EXTM3U
#EXTINF:-1 tvg-id="CBN" tvg-name="CBN" tvg-logo="https://example.com/logo.png" group-title="Notícias",CBN SP
https://streaming.cbn.com.br/cbnsp
#EXTINF:-1 tvg-id="Globo" tvg-name="TV Globo" group-title="Aberto",TV Globo SP
https://globo.com/live/sp
"""
    
    with open(exemplo_path, "w", encoding="utf-8") as f:
        f.write(conteudo)
    
    print(f"  📝 Criado arquivo de exemplo: {exemplo_path}")
    return [{"name": "exemplo.m3u", "url": exemplo_path, "size": len(conteudo)}]

def main():
    """Função principal"""
    print("=" * 50)
    print("🚀 IPTV System - Atualização Automática")
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"👤 Repositório: {REPO_OWNER}/{REPO_NAME}")
    print("=" * 50)
    
    # Listar e baixar arquivos
    arquivos = listar_arquivos()
    
    # Se não encontrou nenhum arquivo, criar um de exemplo
    if not arquivos:
        print("\n⚠️ Nenhum arquivo de playlist encontrado!")
        print("📝 Criando arquivo de exemplo para teste...")
        arquivos = criar_exemplo_playlist()
    
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