#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processador de listas M3U para IPTV System
Autor: Josiel Jefferson
Versão: 2.0
"""

import os
import re
import json
from datetime import datetime

# Regex para extrair atributos
regex_attr = re.compile(r'([\w\-]+)="(.*?)"')

# EPG URLs organizadas
EPG_URLS = [
    "https://m3u4u.com/epg/jq2zy9epr3bwxmgwyxr5",
    "https://m3u4u.com/epg/3wk1y24kx7uzdevxygz7",
    "https://m3u4u.com/epg/782dyqdrqkh1xegen4zp",
    "https://www.open-epg.com/files/brazil1.xml.gz",
    "https://www.open-epg.com/files/brazil2.xml.gz",
    "https://www.open-epg.com/files/brazil3.xml.gz",
    "https://www.open-epg.com/files/brazil4.xml.gz",
    "https://www.open-epg.com/files/portugal1.xml.gz",
    "https://www.open-epg.com/files/portugal2.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_BR1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_PT1.xml.gz"
]

def extrair_atributos(linha):
    """Extrai atributos da linha EXTINF"""
    attrs = dict(regex_attr.findall(linha))
    return {
        "tvg_id": attrs.get("tvg-id", ""),
        "tvg_name": attrs.get("tvg-name", ""),
        "tvg_logo": attrs.get("tvg-logo", ""),
        "group": attrs.get("group-title", "OUTROS")
    }

def extrair_nome(linha):
    """Extrai o nome do canal da linha EXTINF"""
    return linha.split(",")[-1].strip() if "," in linha else "Sem Nome"

def limpar_texto(txt):
    """Limpa texto removendo espaços extras"""
    return txt.strip() if txt else ""

def processar_lista(pasta_entrada, pasta_saida):
    """Processa todas as listas M3U da pasta de entrada"""
    urls_vistas = set()
    canais = []
    stats = {
        "arquivos_processados": 0,
        "canais_encontrados": 0,
        "canais_unicos": 0,
        "erros": 0
    }
    
    # Verificar se pasta existe
    if not os.path.exists(pasta_entrada):
        os.makedirs(pasta_entrada)
        return canais, stats
    
    # Processar cada arquivo
    for arquivo in os.listdir(pasta_entrada):
        if not arquivo.endswith(('.m3u', '.m3u8', '.txt')):
            continue
            
        caminho = os.path.join(pasta_entrada, arquivo)
        stats["arquivos_processados"] += 1
        
        try:
            with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                dados_extinf = None
                
                for linha in f:
                    linha = linha.strip()
                    if not linha:
                        continue
                    
                    if linha.startswith("#EXTINF"):
                        attrs = extrair_atributos(linha)
                        nome = extrair_nome(linha)
                        
                        dados_extinf = {
                            "nome": limpar_texto(nome) or "Sem Nome",
                            "tvg_id": limpar_texto(attrs["tvg_id"]),
                            "tvg_name": limpar_texto(attrs["tvg_name"]) or nome,
                            "tvg_logo": limpar_texto(attrs["tvg_logo"]),
                            "group": limpar_texto(attrs["group"]) or "OUTROS"
                        }
                        
                    elif linha.startswith("http"):
                        if linha not in urls_vistas:
                            urls_vistas.add(linha)
                            
                            canal = dados_extinf.copy() if dados_extinf else {
                                "nome": "Sem Nome",
                                "tvg_id": "",
                                "tvg_name": "Sem Nome",
                                "tvg_logo": "",
                                "group": "OUTROS"
                            }
                            
                            canal["url"] = linha
                            canal["stream_id"] = len(canais) + 1
                            canal["added"] = datetime.now().isoformat()
                            
                            canais.append(canal)
                            stats["canais_unicos"] += 1
                            
                        dados_extinf = None
                        
        except Exception as e:
            print(f"❌ Erro ao processar {arquivo}: {e}")
            stats["erros"] += 1
    
    stats["canais_encontrados"] = len(canais)
    
    # Gerar header M3U
    epg_string = ",".join(EPG_URLS)
    
    header = (
        f'#EXTM3U url-tvg="{epg_string}"\n\n'
        '#PLAYLISTV: '
        'pltv-logo="https://cdn-icons-png.flaticon.com/256/25/25231.png" '
        'pltv-name="☆ IPTV System - Josiel Jefferson ☆" '
        'pltv-description="Playlist automática atualizada via GitHub Actions" '
        'pltv-cover="https://images.icon-icons.com/2407/PNG/512/gitlab_icon_146171.png" '
        'pltv-author="Josiel Jefferson" '
        'pltv-site="https://josieljefferson12.github.io/" '
        'pltv-email="josielluz@proton.me"\n\n'
    )
    
    # Salvar playlist M3U
    caminho_saida = os.path.join(pasta_saida, "playlists.m3u")
    
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(header)
        
        for c in canais:
            f.write(
                f'#EXTINF:-1 tvg-id="{c["tvg_id"]}" '
                f'tvg-name="{c["tvg_name"]}" '
                f'tvg-logo="{c["tvg_logo"]}" '
                f'group-title="{c["group"]}",{c["nome"]}\n'
            )
            f.write(c["url"] + "\n\n")
    
    # Salvar JSON com todos os canais
    caminho_json = os.path.join(pasta_saida, "channels.json")
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(canais, f, indent=2, ensure_ascii=False)
    
    # Salvar estatísticas
    caminho_stats = os.path.join(pasta_saida, "stats.json")
    with open(caminho_stats, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    
    print(f"✅ Processados {stats['canais_unicos']} canais únicos de {stats['arquivos_processados']} arquivos")
    
    return canais, stats