#!/usr/bin/env python3
"""
test_collector_new.py - Script para teste do Sentinel Collector (versão atualizada)

Este script testa o funcionamento do coletor enviando requisições de teste,
suportando todos os tipos de teste disponíveis.

Autor: TriplePlay Team
Data: Maio 2025
"""

import os
import sys
import json
import time
import argparse
import requests
from pprint import pprint

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Testa o Sentinel Collector",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Argumentos básicos
    parser.add_argument("--url", default="http://localhost:5000", help="URL do Sentinel Collector")
    parser.add_argument("--mikrotik", required=True, help="Endereço IP do MikroTik")
    parser.add_argument("--user", required=True, help="Usuário do MikroTik")
    parser.add_argument("--password", required=True, help="Senha do MikroTik")
    parser.add_argument("--target", default="8.8.8.8", help="IP alvo para teste")
    
    # Argumentos para tipos de teste
    parser.add_argument("--test", choices=["ping", "tcp", "traceroute"], default="ping", 
                        help="Tipo de teste a ser executado")
    parser.add_argument("--count", type=int, default=3, help="Número de pings")
    parser.add_argument("--port", type=int, default=80, help="Porta TCP para teste")
    parser.add_argument("--max-hops", type=int, default=30, help="Máximo de hops para traceroute")
    parser.add_argument("--no-cache", action="store_true", help="Desabilita uso de cache")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verboso")
    
    return parser.parse_args()

def check_health(url):
    """Verifica a disponibilidade do serviço"""
    try:
        response = requests.get(f"{url}/api/health")
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
        response = requests.get(f"{url}/api/version")
        if response.status_code == 200:
            print(f"ℹ️ Informações de versão: {response.json()}")
            return True
        else:
            print(f"❌ Erro ao obter versão. Código: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao obter versão: {str(e)}")
        return False

def run_test(url, test_type, mikrotik_host, mikrotik_user, mikrotik_password, target, **kwargs):
    """Executa um teste de conectividade"""
    print(f"🔄 Executando teste de {test_type} para {target} via {mikrotik_host}...")
    
    # Payload básico
    payload = {
        "mikrotik_host": mikrotik_host,
        "mikrotik_user": mikrotik_user,
        "mikrotik_password": mikrotik_password,
        "test_type": test_type,
        "target": target,
        "use_cache": not kwargs.get("no_cache", False)
    }
    
    # Adiciona parâmetros específicos para cada tipo de teste
    if test_type == "ping" and "count" in kwargs:
        payload["count"] = kwargs["count"]
    elif test_type == "tcp" and "port" in kwargs:
        payload["port"] = kwargs["port"]
    elif test_type == "traceroute" and "max_hops" in kwargs:
        payload["max_hops"] = kwargs["max_hops"]
    
    try:
        response = requests.post(f"{url}/api/test", json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            
            # Se modo verboso, imprime a resposta completa
            if kwargs.get("verbose", False):
                print("Resposta completa:")
                print(json.dumps(result, indent=2))
                print()
            
            if result.get("status") == "success":
                # Verifica se o resultado veio do cache
                if result.get("cached", False):
                    print(f"ℹ️ Resultado obtido do cache (timestamp: {result.get('cache_timestamp')})")
                
                # Processa o resultado com base no tipo de teste
                if test_type == "ping" and "ping_stats" in result:
                    display_ping_results(result)
                elif test_type == "tcp" and "tcp_test" in result:
                    display_tcp_results(result)
                elif test_type == "traceroute" and "traceroute" in result:
                    display_traceroute_results(result)
                else:
                    print(f"✅ Teste concluído com sucesso!")
                    print(f"  - Tipo: {test_type}")
                    print(f"  - Alvo: {target}")
                    print(f"  - Timestamp: {result.get('metadata', {}).get('timestamp', 'N/A')}")
                
                return True
            else:
                print(f"❌ Teste falhou: {result.get('message', 'Erro desconhecido')}")
                return False
        else:
            print(f"❌ Requisição falhou com código {response.status_code}")
            try:
                # Tenta extrair mensagem de erro
                error = response.json()
                print(f"Detalhes: {error.get('message', 'Sem detalhes')}")
            except:
                print(f"Resposta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro ao executar teste: {str(e)}")
        return False

def display_ping_results(result):
    """Exibe resultados formatados de teste de ping"""
    ping_stats = result.get("ping_stats", {})
    print(f"✅ Teste de ping concluído com sucesso!")
    print(f"  - Pacotes enviados: {ping_stats.get('sent', 'N/A')}")
    print(f"  - Pacotes recebidos: {ping_stats.get('received', 'N/A')}")
    print(f"  - Perda de pacotes: {ping_stats.get('packet_loss', 'N/A')}%")
    print(f"  - RTT mínimo: {ping_stats.get('min_rtt', 'N/A')}ms")
    print(f"  - RTT médio: {ping_stats.get('avg_rtt', 'N/A')}ms")
    print(f"  - RTT máximo: {ping_stats.get('max_rtt', 'N/A')}ms")
    print(f"  - Timestamp: {result.get('metadata', {}).get('timestamp', 'N/A')}")

def display_tcp_results(result):
    """Exibe resultados formatados de teste TCP"""
    tcp_test = result.get("tcp_test", {})
    status = "SUCESSO" if tcp_test.get('reachable') else "FALHA"
    print(f"✅ Teste de conexão TCP concluído!")
    print(f"  - Status: {status}")
    print(f"  - Alvo: {tcp_test.get('target', 'N/A')}:{tcp_test.get('port', 'N/A')}")
    print(f"  - Mensagem: {tcp_test.get('message', 'N/A')}")
    print(f"  - Timestamp: {result.get('metadata', {}).get('timestamp', 'N/A')}")

def display_traceroute_results(result):
    """Exibe resultados formatados de teste de traceroute"""
    tr = result.get("traceroute", {})
    print(f"✅ Teste de traceroute concluído!")
    print(f"  - Número de hops: {tr.get('hop_count', 'N/A')}")
    print(f"  - Destino alcançado: {'Sim' if tr.get('target_reached') else 'Não'}")
    print(f"  - Timestamp: {result.get('metadata', {}).get('timestamp', 'N/A')}")
    
    print("\nRota:")
    for hop in tr.get("hops", []):
        if hop.get("unreachable"):
            print(f"  {hop['hop']:2d}  * * *  Tempo esgotado")
        else:
            rtt = f"{hop['rtt']:.1f} ms" if hop.get('rtt') is not None else "-- ms"
            ip = hop.get('ip', '*')
            hostname = hop.get('hostname', '')
            print(f"  {hop['hop']:2d}  {ip:15s} {hostname:30s} {rtt}")

def main():
    """Função principal do script"""
    args = parse_args()
    
    # Verifica a saúde do serviço
    if not check_health(args.url):
        print("⚠️ Problemas detectados. Continuando mesmo assim...")
    
    # Obtém informações de versão
    get_version(args.url)
    
    # Executa o teste solicitado
    if args.test == "ping":
        run_test(
            args.url, "ping", args.mikrotik, args.user, args.password, args.target, 
            count=args.count, no_cache=args.no_cache, verbose=args.verbose
        )
    elif args.test == "tcp":
        run_test(
            args.url, "tcp", args.mikrotik, args.user, args.password, args.target, 
            port=args.port, no_cache=args.no_cache, verbose=args.verbose
        )
    elif args.test == "traceroute":
        run_test(
            args.url, "traceroute", args.mikrotik, args.user, args.password, args.target, 
            max_hops=args.max_hops, no_cache=args.no_cache, verbose=args.verbose
        )
    else:
        print(f"❌ Tipo de teste não suportado: {args.test}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
