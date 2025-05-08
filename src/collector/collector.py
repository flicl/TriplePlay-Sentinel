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
from typing import Dict, List, Any, Union, Optional
from datetime import datetime

import paramiko
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Configuração de log
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

# Inicializa a aplicação Flask
app = Flask(__name__)

# Configurações
DEFAULT_TIMEOUT = int(os.getenv('DEFAULT_TIMEOUT', '5'))
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))

# Credenciais padrão para MikroTik (podem ser sobrescritas por requisição)
DEFAULT_MIKROTIK_USER = os.getenv('MIKROTIK_USER', '')
DEFAULT_MIKROTIK_PASSWORD = os.getenv('MIKROTIK_PASSWORD', '')

class MikroTikConnector:
    """Classe para gerenciar conexões com dispositivos MikroTik via SSH/API"""
    
    def __init__(self, host: str, username: str, password: str, port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None
    
    def connect(self) -> bool:
        """Estabelece conexão SSH com o dispositivo MikroTik"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=DEFAULT_TIMEOUT
            )
            logger.info(f"Conexão estabelecida com {self.host}")
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar com {self.host}: {str(e)}")
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
                return {"status": "error", "message": "Falha na conexão com o dispositivo"}
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=DEFAULT_TIMEOUT)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                logger.warning(f"Erro ao executar comando no {self.host}: {error}")
                return {"status": "error", "message": error}
            
            return {"status": "success", "output": output}
        except Exception as e:
            logger.error(f"Erro ao executar comando no {self.host}: {str(e)}")
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


@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificação de saúde do serviço"""
    return jsonify({
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })


@app.route('/test', methods=['POST'])
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
    
    # Validações adicionais
    if not mikrotik_user or not mikrotik_password:
        return jsonify({
            "status": "error", 
            "message": "Credenciais MikroTik não fornecidas (defina no .env ou na requisição)"
        }), 400
    
    # Validar o endereço IP de destino
    try:
        ipaddress.ip_address(target)
    except ValueError:
        return jsonify({"status": "error", "message": f"Endereço IP de destino inválido: {target}"}), 400
    
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
            result = mikrotik.run_ping_test(target, count, size)
        elif test_type == "tcp":
            port = int(data.get('port', 80))
            if not 1 <= port <= 65535:
                return jsonify({"status": "error", "message": f"Porta TCP inválida: {port}"}), 400
            result = mikrotik.run_tcp_connect_test(target, port)
        else:
            return jsonify({
                "status": "error", 
                "message": f"Tipo de teste não suportado: {test_type}. Use 'ping' ou 'tcp'"
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
        "mikrotik_host": mikrotik_host
    }
    
    return jsonify(result)


@app.route('/version', methods=['GET'])
def version():
    """Retorna informações de versão do coletor"""
    return jsonify({
        "name": "Sentinel Collector",
        "version": "1.0.0",
        "description": "Componente central do Sistema Sentinel para monitoramento via MikroTik-Zabbix",
        "author": "TriplePlay Team"
    })


if __name__ == '__main__':
    logger.info(f"Iniciando Sentinel Collector na porta {PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG_MODE)
