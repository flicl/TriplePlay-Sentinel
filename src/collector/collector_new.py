#!/usr/bin/env python3
"""
collector.py - Componente central do Sistema Sentinel

Este script atua como um intermediário entre o Zabbix e dispositivos MikroTik,
permitindo que o Zabbix monitore conectividade de rede usando os roteadores MikroTik
como pontos de teste distribuídos.

Autor: TriplePlay Team
Data: Maio 2025
"""

import os
import sys
import json
import time
import logging
import ipaddress
import re
import threading
from typing import Dict, List, Any, Union, Optional, Tuple
from datetime import datetime
from pathlib import Path

import paramiko
import requests
from flask import Flask, request, jsonify, render_template, send_from_directory, abort
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Configuração básica de logging inicial
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('collector.log')
    ]
)
logger = logging.getLogger('sentinel-collector')

# Carrega variáveis de ambiente
load_dotenv()

# Importa o helper de configuração
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from config_helper import config
    logger.info("Configuração carregada via config_helper")
except ImportError as e:
    logger.error(f"Erro ao importar config_helper: {str(e)}")
    # Configurações básicas em caso de falha
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    DEFAULT_TIMEOUT = int(os.getenv('DEFAULT_TIMEOUT', '5'))
    DEFAULT_MIKROTIK_USER = os.getenv('MIKROTIK_USER', '')
    DEFAULT_MIKROTIK_PASSWORD = os.getenv('MIKROTIK_PASSWORD', '')

# Reconfigura o logging com base nas configurações
try:
    # Atualiza a configuração de logging
    log_level = config.get_log_level()
    log_file = config.get('logging.file', 'collector.log')
    
    # Cria diretório para logs se não existir
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Reinicializa o logger com as novas configurações
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file)
        ]
    )
    logger = logging.getLogger('sentinel-collector')
    logger.info(f"Logging configurado com nível {logging.getLevelName(log_level)}")
except Exception as e:
    logger.error(f"Erro ao configurar logging: {str(e)}")

# Configurações do servidor
DEBUG_MODE = config.get('server.debug', False)
HOST = config.get('server.host', '0.0.0.0')
PORT = config.get('server.port', 5000)
DEFAULT_TIMEOUT = config.get('server.timeout', 5)

# Credenciais padrão para MikroTik
DEFAULT_MIKROTIK_USER = config.get('mikrotik.default_user', '')
DEFAULT_MIKROTIK_PASSWORD = config.get('mikrotik.default_password', '')

# Configurações de cache
CACHE_ENABLED = config.get('cache.enabled', True)
CACHE_TTL = config.get('cache.ttl', 300)

# Inicializa a aplicação Flask
app = Flask(__name__, 
           static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
           template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

# Habilita suporte a CORS
CORS(app)

# Suporte a proxy reverso
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Cache para resultados de testes
# Estrutura: {hash_key: {'timestamp': datetime, 'result': dict}}
results_cache = {}

class MikroTikConnector:
    """Classe para gerenciar conexões com dispositivos MikroTik via SSH/API"""
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        self.connection_attempts = 0
        self.max_attempts = config.get('mikrotik.retry_count', 2)
        self.connection_timeout = config.get('mikrotik.connection_timeout', 10)
    
    def connect(self) -> bool:
        """Estabelece conexão SSH com o dispositivo MikroTik"""
        if self.connection_attempts >= self.max_attempts:
            logger.error(f"Número máximo de tentativas de conexão excedido para {self.host}")
            return False
            
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.connection_timeout
            )
            logger.info(f"Conexão estabelecida com {self.host}")
            self.connection_attempts = 0  # Reset de tentativas após sucesso
            return True
        except Exception as e:
            self.connection_attempts += 1
            logger.error(f"Erro ao conectar com {self.host} (tentativa {self.connection_attempts}): {str(e)}")
            
            if self.connection_attempts < self.max_attempts:
                logger.info(f"Tentando novamente em 2 segundos...")
                time.sleep(2)
                return self.connect()
                
            return False
    
    def disconnect(self) -> None:
        """Encerra a conexão SSH"""
        if self.client:
            self.client.close()
            self.client = None
    
    def execute_command(self, command: str) -> dict:
        """Executa um comando no RouterOS e retorna o resultado"""
        if not self.client:
            if not self.connect():
                return {"status": "error", "message": f"Falha na conexão com o dispositivo {self.host}"}
        
        try:
            logger.debug(f"Executando comando no {self.host}: {command}")
            stdin, stdout, stderr = self.client.exec_command(command, timeout=self.connection_timeout)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                logger.warning(f"Erro ao executar comando no {self.host}: {error}")
                return {"status": "error", "message": error}
            
            return {"status": "success", "output": output}
        except Exception as e:
            logger.error(f"Erro ao executar comando no {self.host}: {str(e)}")
            
            # Tenta reconectar e tentar novamente caso a conexão tenha sido perdida
            if "SSH session not active" in str(e) or "Socket is closed" in str(e):
                logger.info(f"Tentando reconectar com {self.host}")
                self.client = None
                if self.connect():
                    logger.info(f"Reconectado com {self.host}, tentando comando novamente")
                    return self.execute_command(command)
                    
            return {"status": "error", "message": str(e)}
    
    def run_ping_test(self, target: str, count: int = 3, size: int = 64) -> dict:
        """Executa teste de ping a partir do MikroTik"""
        command = f"/ping {target} count={count} size={size}"
        result = self.execute_command(command)
        
        if result["status"] == "error":
            return result
        
        # Processando a saída do ping para extrair valores úteis
        output = result["output"]
        
        # Analisando a saída para extrair estatísticas
        try:
            ping_stats = self._parse_ping_output(output)
            return {"status": "success", "ping_stats": ping_stats}
        except Exception as e:
            logger.error(f"Erro ao processar resultado do ping: {str(e)}")
            return {"status": "error", "message": f"Erro ao processar resultado: {str(e)}", "raw_output": output}
    
    def _parse_ping_output(self, output: str) -> dict:
        """Analisa a saída do comando ping do RouterOS"""
        lines = output.strip().split('\n')
        
        # Valores padrão se não conseguirmos extrair da saída
        sent = 0
        received = 0
        min_time = 0
        avg_time = 0
        max_time = 0
        
        for line in lines:
            line = line.strip()
            if "sent=" in line and "received=" in line:
                # Exemplo: "3 packets sent, 3 received, 0% packet loss"
                parts = line.split(',')
                for part in parts:
                    if "sent=" in part or "sent " in part:
                        sent = int(part.split('=')[1].strip() if '=' in part else part.split(' ')[0].strip())
                    if "received=" in part or "received " in part:
                        received = int(part.split('=')[1].strip() if '=' in part else part.split(' ')[0].strip())
            
            if "min-rtt=" in line or "min/avg/max" in line:
                # Exemplo: "min-rtt=1ms, avg-rtt=1ms, max-rtt=1ms"
                # ou "round-trip min/avg/max = 10.123/15.345/20.567 ms"
                if "min-rtt=" in line:
                    parts = line.split(',')
                    for part in parts:
                        if "min-rtt=" in part:
                            min_time = float(part.split('=')[1].replace('ms', '').strip())
                        if "avg-rtt=" in part:
                            avg_time = float(part.split('=')[1].replace('ms', '').strip())
                        if "max-rtt=" in part:
                            max_time = float(part.split('=')[1].replace('ms', '').strip())
                elif "min/avg/max" in line:
                    # Formato alternativo encontrado em algumas versões
                    time_part = line.split('=')[1].strip()
                    times = time_part.split('/') 
                    if len(times) >= 3:
                        min_time = float(times[0].strip())
                        avg_time = float(times[1].strip())
                        max_time = float(times[2].replace('ms', '').strip())
        
        # Calcula a perda de pacotes
        packet_loss = 0
        if sent > 0:
            packet_loss = round(((sent - received) / sent) * 100, 2)
        
        return {
            "sent": sent,
            "received": received,
            "packet_loss": packet_loss,
            "min_rtt": min_time,
            "avg_rtt": avg_time,
            "max_rtt": max_time
        }
    
    def run_tcp_connect_test(self, target: str, port: int) -> dict:
        """Executa teste de conexão TCP a partir do MikroTik"""
        # Usa o comando telnet para testar a conexão TCP
        command = f"/system telnet {target} {port}"
        result = self.execute_command(command + " quit")
        
        if "Connected to" in result.get("output", ""):
            return {
                "status": "success", 
                "tcp_test": {
                    "reachable": True,
                    "target": target,
                    "port": port,
                    "message": "Conexão TCP estabelecida com sucesso"
                }
            }
        else:
            return {
                "status": "success", 
                "tcp_test": {
                    "reachable": False,
                    "target": target,
                    "port": port,
                    "message": "Não foi possível estabelecer conexão TCP"
                }
            }
    
    def run_traceroute_test(self, target: str, max_hops: int = 30) -> dict:
        """Executa teste de traceroute a partir do MikroTik"""
        command = f"/tool traceroute {target} count=1 max-hops={max_hops} timeout=3"
        result = self.execute_command(command)
        
        if result["status"] == "error":
            return result
        
        output = result["output"]
        
        # Analisa a saída do traceroute
        try:
            traceroute_data = self._parse_traceroute_output(output)
            return {"status": "success", "traceroute": traceroute_data}
        except Exception as e:
            logger.error(f"Erro ao processar resultado do traceroute: {str(e)}")
            return {"status": "error", "message": f"Erro ao processar resultado: {str(e)}", "raw_output": output}
    
    def _parse_traceroute_output(self, output: str) -> dict:
        """Analisa a saída do comando traceroute do RouterOS"""
        lines = output.strip().split('\n')
        hops = []
        
        # Padrão para extrair informações do hop
        hop_pattern = re.compile(r'^\s*(\d+)\s+(?:(\d+\.\d+\.\d+\.\d+)|(\*))(?:\s+([\d\.]+)ms)?(?:\s+([\d\.]+)ms)?(?:\s+([\d\.]+)ms)?')
        
        for line in lines:
            match = hop_pattern.match(line)
            if match:
                hop_num = int(match.group(1))
                ip = match.group(2) if match.group(2) else None
                
                # Coleta os tempos disponíveis (podem ser 1, 2 ou 3 pacotes)
                times = []
                for i in range(4, 7):
                    if match.group(i):
                        try:
                            times.append(float(match.group(i)))
                        except (ValueError, TypeError):
                            pass
                
                # Calcula a média dos tempos se houver tempos disponíveis
                avg_time = sum(times) / len(times) if times else None
                
                hop = {
                    "hop": hop_num,
                    "ip": ip,
                    "unreachable": ip is None,
                    "rtt": avg_time,
                    "rtt_samples": times
                }
                
                # Adiciona informações de resolução DNS se estiver disponível na saída
                hostname_match = re.search(rf"{ip}\s+([^\s]+)", line) if ip else None
                if hostname_match:
                    hop["hostname"] = hostname_match.group(1)
                
                hops.append(hop)
        
        return {
            "hops": hops,
            "hop_count": len(hops),
            "target_reached": any(hop.get("ip") for hop in hops[-2:]) if hops else False
        }


def get_cache_key(test_type: str, target: str, **params) -> str:
    """Gera uma chave de cache única para um teste"""
    param_str = ";".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"{test_type}:{target}:{param_str}"


def is_cached_result_valid(cache_key: str) -> bool:
    """Verifica se um resultado em cache ainda é válido"""
    if not CACHE_ENABLED:
        return False
        
    if cache_key not in results_cache:
        return False
        
    cached_time = results_cache[cache_key]['timestamp']
    now = datetime.now()
    
    # Retorna True se o cache ainda for válido
    return (now - cached_time).total_seconds() < CACHE_TTL


@app.route('/')
def index():
    """Renderiza a página inicial do collector (dashboard)"""
    return render_template('index.html', version="1.0.0")


@app.route('/static/<path:path>')
def send_static(path):
    """Serve arquivos estáticos"""
    return send_from_directory(app.static_folder, path)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint para verificação de saúde do serviço"""
    return jsonify({
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "uptime": time.time() - app.config.get('start_time', time.time())
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    """Retorna configurações públicas do collector"""
    # Filtra apenas configurações seguras para expor
    safe_config = {
        "server": {
            "host": HOST,
            "port": PORT
        },
        "cache": {
            "enabled": CACHE_ENABLED,
            "ttl": CACHE_TTL
        },
        "features": {
            "ping": True,
            "tcp": True,
            "traceroute": True
        }
    }
    return jsonify(safe_config)


@app.route('/api/test', methods=['POST'])
def run_test():
    """Endpoint principal para executar testes de conectividade"""
    data = request.json
    
    if not data:
        return jsonify({"status": "error", "message": "Dados de requisição inválidos"}), 400
    
    # Validação dos campos obrigatórios
    required_fields = ['mikrotik_host', 'test_type', 'target']
    for field in required_fields:
        if field not in data:
            return jsonify({"status": "error", "message": f"Campo obrigatório ausente: {field}"}), 400
    
    # Extrai os parâmetros
    mikrotik_host = data['mikrotik_host']
    test_type = data['test_type']
    target = data['target']
    
    # Parâmetros opcionais
    mikrotik_user = data.get('mikrotik_user', DEFAULT_MIKROTIK_USER)
    mikrotik_password = data.get('mikrotik_password', DEFAULT_MIKROTIK_PASSWORD)
    mikrotik_port = int(data.get('mikrotik_port', 22))
    use_cache = data.get('use_cache', True) and CACHE_ENABLED
    
    # Validações adicionais
    if not mikrotik_user or not mikrotik_password:
        return jsonify({
            "status": "error", 
            "message": "Credenciais MikroTik não fornecidas (defina no .env ou na requisição)"
        }), 400
    
    # Validar o endereço IP ou hostname de destino
    try:
        # Se for um IP, valida; se for hostname, prossegue
        try:
            ipaddress.ip_address(target)
        except ValueError:
            # Não é um IP válido, assume que é um hostname
            if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]{0,61}[a-zA-Z0-9])?$', target):
                return jsonify({"status": "error", "message": f"Hostname de destino inválido: {target}"}), 400
    except Exception:
        return jsonify({"status": "error", "message": f"Destino inválido: {target}"}), 400
    
    # Verifica se resultado está em cache
    cache_params = {k: v for k, v in data.items() if k not in ['mikrotik_host', 'mikrotik_user', 'mikrotik_password', 'use_cache']}
    cache_key = get_cache_key(test_type, target, **cache_params)
    
    if use_cache and is_cached_result_valid(cache_key):
        cached_result = results_cache[cache_key]['result']
        cached_result["cached"] = True
        cached_result["cache_timestamp"] = results_cache[cache_key]['timestamp'].isoformat()
        return jsonify(cached_result)
    
    # Inicializa o conector MikroTik
    mikrotik = MikroTikConnector(
        host=mikrotik_host,
        username=mikrotik_user,
        password=mikrotik_password,
        port=mikrotik_port
    )
    
    # Executa o teste solicitado
    try:
        if test_type == "ping":
            count = int(data.get('count', 3))
            size = int(data.get('size', 64))
            
            if not 1 <= count <= 100:
                return jsonify({"status": "error", "message": f"Número de pings inválido: {count}. Use entre 1 e 100."}), 400
            if not 16 <= size <= 65535:
                return jsonify({"status": "error", "message": f"Tamanho de pacote inválido: {size}. Use entre 16 e 65535."}), 400
                
            result = mikrotik.run_ping_test(target, count, size)
            
        elif test_type == "tcp":
            port = int(data.get('port', 80))
            if not 1 <= port <= 65535:
                return jsonify({"status": "error", "message": f"Porta TCP inválida: {port}. Use entre 1 e 65535."}), 400
            result = mikrotik.run_tcp_connect_test(target, port)
            
        elif test_type == "traceroute":
            max_hops = int(data.get('max_hops', 30))
            if not 1 <= max_hops <= 64:
                return jsonify({"status": "error", "message": f"Número máximo de hops inválido: {max_hops}. Use entre 1 e 64."}), 400
            result = mikrotik.run_traceroute_test(target, max_hops)
            
        else:
            return jsonify({
                "status": "error", 
                "message": f"Tipo de teste não suportado: {test_type}. Use 'ping', 'tcp' ou 'traceroute'."
            }), 400
    except Exception as e:
        logger.error(f"Erro ao executar teste {test_type} para {target} via {mikrotik_host}: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": f"Erro ao executar teste: {str(e)}"
        }), 500
    finally:
        # Garante que a conexão seja fechada
        mikrotik.disconnect()
    
    # Adiciona metadados ao resultado
    result["metadata"] = {
        "timestamp": datetime.now().isoformat(),
        "test_type": test_type,
        "target": target,
        "mikrotik_host": mikrotik_host,
        "cache_key": cache_key
    }
    
    # Armazena resultado em cache se for bem-sucedido
    if result.get("status") == "success" and CACHE_ENABLED:
        results_cache[cache_key] = {
            'timestamp': datetime.now(),
            'result': result
        }
    
    return jsonify(result)


@app.route('/api/version', methods=['GET'])
def version():
    """Retorna informações de versão do coletor"""
    return jsonify({
        "name": "Sentinel Collector",
        "version": "1.0.0",
        "description": "Componente central do Sistema Sentinel para monitoramento via MikroTik-Zabbix",
        "author": "TriplePlay Team",
        "date": "Maio 2025"
    })


@app.route('/api/stats', methods=['GET'])
def statistics():
    """Retorna estatísticas do collector"""
    cache_size = len(results_cache)
    cache_items = []
    
    for key, value in results_cache.items():
        age = (datetime.now() - value['timestamp']).total_seconds()
        test_type, target, _ = key.split(':', 2)
        
        cache_items.append({
            "key": key,
            "test_type": test_type,
            "target": target,
            "age_seconds": age,
            "timestamp": value['timestamp'].isoformat()
        })
    
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - app.config.get('start_time', time.time()),
        "cache": {
            "enabled": CACHE_ENABLED,
            "ttl": CACHE_TTL,
            "size": cache_size,
            "items": cache_items[:10]  # Limita a 10 itens para não sobrecarregar
        }
    })


def clean_expired_cache():
    """Limpa itens expirados do cache periodicamente"""
    if not CACHE_ENABLED:
        return
        
    global results_cache
    now = datetime.now()
    
    # Filtra itens não expirados
    valid_items = {}
    expired_count = 0
    
    for key, value in results_cache.items():
        if (now - value['timestamp']).total_seconds() < CACHE_TTL:
            valid_items[key] = value
        else:
            expired_count += 1
    
    results_cache = valid_items
    
    if expired_count > 0:
        logger.debug(f"Limpeza de cache: {expired_count} itens expirados removidos.")
    
    # Agenda próxima limpeza
    threading.Timer(CACHE_TTL / 2, clean_expired_cache).start()


def init_app():
    """Inicializa a aplicação com configurações e tarefas"""
    # Registra o horário de início
    app.config['start_time'] = time.time()
    
    # Cria diretórios necessários
    log_dir = os.path.dirname(config.get('logging.file', 'collector.log'))
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Inicia tarefa de limpeza de cache
    if CACHE_ENABLED:
        clean_expired_cache()
    
    # Registra o horário de inicialização
    logger.info(f"Sentinel Collector v1.0.0 iniciado em {datetime.now().isoformat()}")
    
    return app


if __name__ == '__main__':
    # Inicializa a aplicação
    app = init_app()
    
    # Obtém configurações do servidor
    server_settings = {
        'host': HOST,
        'port': PORT,
        'debug': DEBUG_MODE
    }
    
    # Adiciona SSL context se estiver configurado
    ssl_cert = config.get('server.ssl_cert')
    ssl_key = config.get('server.ssl_key')
    if ssl_cert and ssl_key and os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        server_settings['ssl_context'] = (ssl_cert, ssl_key)
        logger.info(f"HTTPS habilitado com certificado {ssl_cert}")
    
    # Registra mensagem de inicialização
    logger.info(f"Iniciando servidor em {server_settings['host']}:{server_settings['port']}")
    
    # Inicia o servidor Flask
    app.run(**server_settings)
