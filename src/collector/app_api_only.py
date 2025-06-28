#!/usr/bin/env python3
"""
TriplePlay-Sentinel Collector - API-Only Application
Sistema de Monitoramento 100% baseado na API MikroTik (sem SSH)

Este é o módulo principal otimizado para máxima performance e concorrência
usando exclusivamente a API REST do MikroTik.
"""

import os
import sys
import time
import signal
import atexit
import logging
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from functools import wraps
import json

# Adiciona o diretório do collector ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports do projeto
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from config_api_only import config_api
from mikrotik_librouteros import MikroTikConnector

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, config_api.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config_api.LOG_FILE) if config_api.LOG_FILE else logging.NullHandler()
    ]
)
logger = logging.getLogger('sentinel-api-collector')

# Inicialização do Flask
app = Flask(__name__)
CORS(app)

# Inicializa o pool de conexões MikroTik
mikrotik_connector = MikroTikConnector(
    pool_size=config_api.POOL_SIZE,
    timeout=config_api.TIMEOUT,
    max_batch_size=config_api.MAX_BATCH_SIZE
)

# Estatísticas globais da aplicação
app_stats = {
    'start_time': datetime.now(),
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'active_requests': 0,
    'avg_response_time': 0.0,
    'total_response_time': 0.0,
    'peak_concurrent_requests': 0
}

# Lock para estatísticas thread-safe
stats_lock = threading.RLock()


def update_app_stats(execution_time: float, success: bool):
    """Atualiza estatísticas da aplicação de forma thread-safe"""
    with stats_lock:
        app_stats['total_requests'] += 1
        if success:
            app_stats['successful_requests'] += 1
        else:
            app_stats['failed_requests'] += 1
        
        app_stats['total_response_time'] += execution_time
        app_stats['avg_response_time'] = (
            app_stats['total_response_time'] / app_stats['total_requests']
        )


def track_request_stats(f):
    """Decorator para rastrear estatísticas de requisições"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = datetime.now()
        
        with stats_lock:
            app_stats['active_requests'] += 1
            if app_stats['active_requests'] > app_stats['peak_concurrent_requests']:
                app_stats['peak_concurrent_requests'] = app_stats['active_requests']
        
        try:
            result = f(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Determina sucesso baseado no status code
            if hasattr(result, 'status_code'):
                success = 200 <= result.status_code < 400
            elif isinstance(result, tuple):
                success = 200 <= result[1] < 400
            else:
                success = True
            
            update_app_stats(execution_time, success)
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            update_app_stats(execution_time, False)
            raise
        finally:
            with stats_lock:
                app_stats['active_requests'] -= 1
    
    return decorated_function


@app.route('/health', methods=['GET'])
@track_request_stats
def health_check():
    """Endpoint de health check da aplicação"""
    uptime = datetime.now() - app_stats['start_time']
    
    return jsonify({
        'status': 'healthy',
        'service': 'TriplePlay-Sentinel API-Only Collector',
        'version': '2.0.0',
        'uptime_seconds': uptime.total_seconds(),
        'timestamp': datetime.now().isoformat(),
        'mode': 'API-Only (No SSH)',
        'performance': {
            'total_requests': app_stats['total_requests'],
            'active_requests': app_stats['active_requests'],
            'success_rate_percent': (
                (app_stats['successful_requests'] / max(1, app_stats['total_requests'])) * 100
            ),
            'avg_response_time_seconds': app_stats['avg_response_time']
        }
    })


@app.route('/api/v2/mikrotik/ping', methods=['POST'])
@track_request_stats
def ping_targets():
    """
    Executa ping em targets via API MikroTik (substitui SSH)
    
    Body JSON:
    {
        "host": "192.168.1.1",
        "username": "admin", 
        "password": "password",
        "targets": ["8.8.8.8", "1.1.1.1"],
        "count": 4,
        "use_cache": true
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        # Validação de parâmetros obrigatórios
        required_fields = ['host', 'username', 'password', 'targets']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        host = data['host']
        username = data['username']
        password = data['password']
        targets = data['targets']
        count = data.get('count', 4)
        use_cache = data.get('use_cache', True)
        
        if not isinstance(targets, list) or not targets:
            return jsonify({'error': 'Targets deve ser uma lista não vazia'}), 400
        
        # Cria comandos de ping para execução em lote
        ping_commands = []
        for target in targets:
            ping_commands.append({
                'command': '/ping',
                'parameters': {
                    'address': target,
                    'count': str(count)
                },
                'use_cache': use_cache and count <= 4  # Cache apenas para pings pequenos
            })
        
        # Executa todos os pings em paralelo via API
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        batch_results = loop.run_until_complete(
            mikrotik_connector.execute_batch_ping(
                host=host,
                username=username,
                password=password,
                targets=targets,
                count=count,
                use_cache=use_cache and count <= 4
            )
        )
        
        # Processa resultados
        ping_results = {}
        total_execution_time = 0
        successful_pings = 0
        
        for i, result in enumerate(batch_results):
            target = targets[i]
            if result['status'] == 'success':
                successful_pings += 1
                ping_results[target] = {
                    'status': 'success',
                    'data': result.get('data', {}),
                    'execution_time_seconds': result.get('execution_time_seconds', 0),
                    'cached': result.get('cached', False)
                }
            else:
                ping_results[target] = {
                    'status': 'error',
                    'error': result.get('error', 'Erro desconhecido'),
                    'execution_time_seconds': result.get('execution_time_seconds', 0)
                }
            
            total_execution_time += result.get('execution_time_seconds', 0)
        
        return jsonify({
            'status': 'completed',
            'method': 'API_BATCH',
            'host': host,
            'targets_requested': len(targets),
            'targets_successful': successful_pings,
            'total_execution_time_seconds': max(
                total_execution_time / len(targets),  # Média devido ao paralelismo
                max(r.get('execution_time_seconds', 0) for r in batch_results)
            ),
            'results': ping_results,
            'timestamp': datetime.now().isoformat(),
            'performance_improvement': f'~{len(targets)}x faster than sequential'
        })
        
    except Exception as e:
        logger.error(f"Erro no endpoint ping: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/v2/mikrotik/command', methods=['POST'])
@track_request_stats
def execute_command():
    """
    Executa comando genérico via API MikroTik
    
    Body JSON:
    {
        "host": "192.168.1.1",
        "username": "admin",
        "password": "password", 
        "command": "/system/identity/print",
        "parameters": {},
        "use_cache": true
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        # Validação
        required_fields = ['host', 'username', 'password', 'command']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        # Executa comando via API
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            mikrotik_connector.execute_single_command(
                host=data['host'],
                username=data['username'],
                password=data['password'],
                command=data['command'],
                parameters=data.get('parameters', {}),
                use_cache=data.get('use_cache', True)
            )
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro no endpoint command: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/v2/mikrotik/batch', methods=['POST'])
@track_request_stats
def execute_batch():
    """
    Executa múltiplos comandos em paralelo
    
    Body JSON:
    {
        "host": "192.168.1.1",
        "username": "admin",
        "password": "password",
        "commands": [
            {"command": "/system/identity/print", "parameters": {}},
            {"command": "/interface/print", "parameters": {}}
        ],
        "max_concurrent": 10
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        # Validação
        required_fields = ['host', 'username', 'password', 'commands']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        commands = data['commands']
        if not isinstance(commands, list) or not commands:
            return jsonify({'error': 'Commands deve ser uma lista não vazia'}), 400
        
        max_concurrent = min(
            data.get('max_concurrent', config_api.MAX_CONCURRENT_COMMANDS),
            config_api.MAX_CONCURRENT_COMMANDS
        )
        
        # Executa batch via API
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        results = loop.run_until_complete(
            mikrotik_connector.execute_batch_commands(
                host=data['host'],
                username=data['username'],
                password=data['password'],
                commands=commands,
                max_concurrent=max_concurrent
            )
        )
        
        # Calcula estatísticas
        successful_commands = sum(1 for r in results if r.get('status') == 'success')
        total_execution_time = max(r.get('execution_time_seconds', 0) for r in results)
        
        return jsonify({
            'status': 'completed',
            'method': 'API_BATCH_PARALLEL',
            'commands_requested': len(commands),
            'commands_successful': successful_commands,
            'max_concurrent': max_concurrent,
            'total_execution_time_seconds': total_execution_time,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro no endpoint batch: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/v2/mikrotik/multi-host', methods=['POST'])
@track_request_stats
def execute_multi_host():
    """
    Executa comando em múltiplos MikroTiks simultaneamente
    
    Body JSON:
    {
        "hosts": [
            {"host": "192.168.1.1", "username": "admin", "password": "pass1"},
            {"host": "192.168.1.2", "username": "admin", "password": "pass2"}
        ],
        "command": "/system/identity/print",
        "parameters": {},
        "max_concurrent_hosts": 20
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        # Validação
        required_fields = ['hosts', 'command']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        hosts = data['hosts']
        if not isinstance(hosts, list) or not hosts:
            return jsonify({'error': 'Hosts deve ser uma lista não vazia'}), 400
        
        command = data['command']
        parameters = data.get('parameters', {})
        max_concurrent_hosts = min(
            data.get('max_concurrent_hosts', config_api.MAX_CONCURRENT_HOSTS),
            config_api.MAX_CONCURRENT_HOSTS
        )
        
        # Executa em múltiplos hosts
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        results = loop.run_until_complete(
            mikrotik_connector.execute_multiple_hosts(
                hosts_config=hosts,
                command=command,
                parameters=parameters,
                max_concurrent_hosts=max_concurrent_hosts
            )
        )
        
        # Calcula estatísticas
        successful_hosts = sum(1 for r in results.values() if r.get('status') == 'success')
        
        return jsonify({
            'status': 'completed',
            'method': 'API_MULTI_HOST_PARALLEL',
            'hosts_requested': len(hosts),
            'hosts_successful': successful_hosts,
            'max_concurrent_hosts': max_concurrent_hosts,
            'command': command,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro no endpoint multi-host: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/v2/test-connection', methods=['POST'])
@track_request_stats
def test_connection():
    """
    Testa conectividade com MikroTik via API
    
    Body JSON:
    {
        "host": "192.168.1.1",
        "username": "admin",
        "password": "password",
        "port": 8728,
        "use_ssl": true
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        # Validação
        required_fields = ['host', 'username', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        # Testa conexão
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            mikrotik_connector.test_connection(
                host=data['host'],
                username=data['username'],
                password=data['password'],
                port=data.get('port', config_api.MIKROTIK_API_PORT),
                use_ssl=data.get('use_ssl', config_api.MIKROTIK_USE_SSL)
            )
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro no endpoint test-connection: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/v2/stats', methods=['GET'])
@track_request_stats
def get_stats():
    """Retorna estatísticas completas do sistema"""
    try:
        app_uptime = datetime.now() - app_stats['start_time']
        
        return jsonify({
            'application': {
                'service': 'TriplePlay-Sentinel API-Only Collector',
                'version': '2.0.0',
                'mode': 'API-Only (No SSH)',
                'uptime_seconds': app_uptime.total_seconds(),
                'start_time': app_stats['start_time'].isoformat(),
                'total_requests': app_stats['total_requests'],
                'successful_requests': app_stats['successful_requests'],
                'failed_requests': app_stats['failed_requests'],
                'active_requests': app_stats['active_requests'],
                'peak_concurrent_requests': app_stats['peak_concurrent_requests'],
                'success_rate_percent': (
                    (app_stats['successful_requests'] / max(1, app_stats['total_requests'])) * 100
                ),
                'avg_response_time_seconds': app_stats['avg_response_time']
            },
            'mikrotik_connector': mikrotik_connector.get_stats(),
            'configuration': {
                'max_concurrent_hosts': config_api.MAX_CONCURRENT_HOSTS,
                'max_concurrent_commands': config_api.MAX_CONCURRENT_COMMANDS,
                'max_connections_per_host': config_api.MAX_CONNECTIONS_PER_HOST,
                'cache_ttl_seconds': config_api.CACHE_TTL,
                'mikrotik_timeout': config_api.TIMEOUT,
                'mikrotik_use_ssl': config_api.MIKROTIK_USE_SSL
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro no endpoint stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/v2/cache/clear', methods=['POST'])
@track_request_stats
def clear_cache():
    """Limpa cache do sistema"""
    try:
        mikrotik_connector.clear_cache()
        return jsonify({
            'status': 'success',
            'message': 'Cache limpo com sucesso',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/', methods=['GET'])
def index():
    """Página inicial com informações do sistema"""
    uptime = datetime.now() - app_stats['start_time']
    
    return jsonify({
        'service': 'TriplePlay-Sentinel API-Only Collector',
        'version': '2.0.0',
        'description': 'Sistema de Monitoramento 100% baseado na API MikroTik (sem SSH)',
        'mode': 'API-Only',
        'performance': 'Máxima concorrência e performance',
        'uptime_seconds': uptime.total_seconds(),
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'ping': '/api/v2/mikrotik/ping',
            'command': '/api/v2/mikrotik/command',
            'batch': '/api/v2/mikrotik/batch',
            'multi-host': '/api/v2/mikrotik/multi-host',
            'test-connection': '/api/v2/test-connection',
            'stats': '/api/v2/stats',
            'clear-cache': '/api/v2/cache/clear'
        },
        'timestamp': datetime.now().isoformat()
    })


def cleanup_on_exit():
    """Limpeza ao encerrar a aplicação"""
    logger.info("Encerrando TriplePlay-Sentinel API-Only Collector...")
    
    # Fecha todas as sessões HTTP
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(mikrotik_connector.close_all_connections())
    
    logger.info("Aplicação encerrada com sucesso")


def signal_handler(signum, frame):
    """Handler para sinais do sistema"""
    logger.info(f"Recebido sinal {signum}, encerrando aplicação...")
    cleanup_on_exit()
    sys.exit(0)


# Registra handlers de limpeza
atexit.register(cleanup_on_exit)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


if __name__ == '__main__':
    logger.info("Iniciando TriplePlay-Sentinel API-Only Collector v2.0.0")
    logger.info(f"Modo: API-Only (100% MikroTik API, sem SSH)")
    logger.info(f"Concorrência máxima: {config_api.MAX_CONCURRENT_HOSTS} hosts, {config_api.MAX_CONCURRENT_COMMANDS} comandos")
    logger.info(f"Cache TTL: {config_api.CACHE_TTL}s")
    logger.info(f"API MikroTik: {'HTTPS' if config_api.MIKROTIK_USE_SSL else 'HTTP'}:{config_api.MIKROTIK_API_PORT}")
    
    try:
        app.run(
            host=config_api.API_HOST,
            port=config_api.API_PORT,
            debug=config_api.DEBUG,
            threaded=True
        )
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicação: {str(e)}")
        cleanup_on_exit()
        sys.exit(1)
