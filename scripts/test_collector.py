#!/usr/bin/env python3
"""
test_collector.py - Script para teste do Sentinel Collector

Este script testa o funcionamento do coletor enviando requisições de teste.

Autor: TriplePlay Team
Data: Maio 2025
"""

import os
import sys
import json
import time
import argparse
import requests

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Testa o Sentinel Collector")
    parser.add_argument("--url", default="http://localhost:5000", help="URL do Sentinel Collector")
    parser.add_argument("--mikrotik", required=True, help="Endereço IP do MikroTik")
    parser.add_argument("--user", required=True, help="Usuário do MikroTik")
    parser.add_argument("--password", required=True, help="Senha do MikroTik")
    parser.add_argument("--target", default="8.8.8.8", help="IP alvo para teste de ping")
    parser.add_argument("--count", type=int, default=3, help="Número de pings")
    
    return parser.parse_args()

def check_health(url):
    """Verifica a disponibilidade do serviço"""
    try:
        response = requests.get(f"{url}/health")
        if response.status_code == 200:
            print(f"✅ Serviço disponível: {response.json()}")
            return True
        else:
            print(f"❌ Serviço indisponível. Código: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar com o serviço: {str(e)}")
        return False

def get_version(url):
    """Obtém informações de versão"""
    try:
        response = requests.get(f"{url}/version")
        if response.status_code == 200:
            print(f"ℹ️ Informações de versão: {response.json()}")
            return True
        else:
            print(f"❌ Erro ao obter versão. Código: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao obter versão: {str(e)}")
        return False

def run_ping_test(url, mikrotik_host, mikrotik_user, mikrotik_password, target, count):
    """Executa um teste de ping"""
    print(f"🔄 Executando teste de ping para {target} via {mikrotik_host}...")
    
    payload = {
        "mikrotik_host": mikrotik_host,
        "mikrotik_user": mikrotik_user,
        "mikrotik_password": mikrotik_password,
        "test_type": "ping",
        "target": target,
        "count": count
    }
    
    try:
        response = requests.post(f"{url}/test", json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                ping_stats = result.get("ping_stats", {})
                print(f"✅ Teste concluído com sucesso!")
                print(f"  - Pacotes enviados: {ping_stats.get('sent', 'N/A')}")
                print(f"  - Pacotes recebidos: {ping_stats.get('received', 'N/A')}")
                print(f"  - Perda de pacotes: {ping_stats.get('packet_loss', 'N/A')}%")
                print(f"  - RTT mínimo: {ping_stats.get('min_rtt', 'N/A')}ms")
                print(f"  - RTT médio: {ping_stats.get('avg_rtt', 'N/A')}ms")
                print(f"  - RTT máximo: {ping_stats.get('max_rtt', 'N/A')}ms")
                print(f"  - Timestamp: {result.get('metadata', {}).get('timestamp', 'N/A')}")
                return True
            else:
                print(f"❌ Teste falhou: {result.get('message', 'Erro desconhecido')}")
                return False
        else:
            print(f"❌ Erro na requisição: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao executar teste: {str(e)}")
        return False

def main():
    """Função principal"""
    args = parse_args()
    
    # Verifica saúde do serviço
    if not check_health(args.url):
        sys.exit(1)
    
    # Obtém informações de versão
    get_version(args.url)
    
    # Executa teste de ping
    run_ping_test(
        args.url, 
        args.mikrotik, 
        args.user, 
        args.password, 
        args.target, 
        args.count
    )

if __name__ == "__main__":
    main()
