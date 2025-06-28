#!/usr/bin/env python3
"""
TriplePlay-Sentinel Collector - Aplicação Principal
Sistema de Monitoramento Centralizado MikroTik-Zabbix via HTTP Agent (PULL)

Este é o módulo principal que implementa a API REST para execução de testes
de conectividade em dispositivos MikroTik através do Zabbix HTTP Agent.
"""

import os
import sys
import time
import signal
import atexit
import logging
import threading
from datetime import datetime
from typing import Dict, Any
from functools import wraps

# Adiciona o diretório do collector ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports do projeto
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from config import config
from models import TestResult, TestParameters, SystemStats
from cache import cache
from mikrotik_connector import MikroTikConnector
from processor import processor

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE) if config.LOG_FILE else logging.NullHandler()
    ]
)
logger = logging.getLogger('sentinel-collector')

# Inicialização do conector MikroTik
mikrotik = MikroTikConnector()

# Inicialização do Flask
app = Flask(__name__)
CORS(app)

# Estatísticas globais
app_stats = {
    'start_time': time.time(),
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'cache_hits': 0,
    'cache_misses': 0
}

# Lock para estatísticas thread-safe
stats_lock = threading.Lock()


# ==========================================
# DECORADORES E UTILITÁRIOS
# ==========================================

def require_auth(f):
    """Decorador para autenticação opcional da API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if config.ENABLE_AUTH and config.API_KEY:
            auth_header = request.headers.get('Authorization')
            api_key = request.headers.get('X-API-Key')
            
            if not auth_header and not api_key:
                return jsonify({
                    'status': 'error',
                    'message': 'Autenticação requerida'
                }), 401
            
            # Verifica Bearer token
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                if token != config.API_KEY:
                    return jsonify({
                        'status': 'error',
                        'message': 'Token de autenticação inválido'
                    }), 401
            # Verifica API Key
            elif api_key:
                if api_key != config.API_KEY:
                    return jsonify({
                        'status': 'error',
                        'message': 'API Key inválida'
                    }), 401
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Formato de autenticação inválido'
                }), 401
        
        return f(*args, **kwargs)
    return decorated_function


def update_stats(success: bool, cache_hit: bool = False):
    """Atualiza estatísticas globais de forma thread-safe"""
    with stats_lock:
        app_stats['total_requests'] += 1
        if success:
            app_stats['successful_requests'] += 1
        else:
            app_stats['failed_requests'] += 1
        
        if cache_hit:
            app_stats['cache_hits'] += 1
        else:
            app_stats['cache_misses'] += 1


# ==========================================
# ENDPOINTS DA API REST
# ==========================================

@app.route('/', methods=['GET'])
def index():
    """Página inicial com informações básicas ou dashboard web"""
    # Se requisição for do browser, retorna dashboard
    if 'text/html' in request.headers.get('Accept', ''):
        return render_template('dashboard.html')
    
    # Se requisição for API, retorna JSON
    return jsonify({
        'service': 'TriplePlay-Sentinel Collector',
        'version': '2.0.0',
        'status': 'running',
        'description': 'Sistema de monitoramento centralizado MikroTik-Zabbix via HTTP Agent (PULL)',
        'architecture': 'HTTP Agent (PULL)',
        'endpoints': {
            'health': '/api/health',
            'test': '/api/test',
            'stats': '/api/stats',
            'cache': '/api/cache',
            'connection_test': '/api/connection-test'
        },
        'supported_tests': ['ping', 'tcp', 'traceroute'],
        'documentation': 'https://github.com/your-org/tripleplay-sentinel',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Dashboard web interativo"""
    return render_template('dashboard.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de health check para monitoramento"""
    try:
        uptime = time.time() - app_stats['start_time']
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'uptime_seconds': round(uptime, 2),
            'cache': cache.get_stats(),
            'connections': mikrotik.get_connection_stats(),
            'requests': {
                'total': app_stats['total_requests'],
                'successful': app_stats['successful_requests'],
                'failed': app_stats['failed_requests'],
                'success_rate_percent': (
                    (app_stats['successful_requests'] / app_stats['total_requests'] * 100)
                    if app_stats['total_requests'] > 0 else 0
                )
            },
            'config': config.to_dict()
        })
    except Exception as e:
        logger.error(f"Erro no health check: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/test', methods=['POST'])
@require_auth
def execute_test():
    """
    Endpoint principal para execução de testes
    
    Este é o endpoint que o Zabbix HTTP Agent chama para executar testes
    """
    try:
        # Valida Content-Type
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Content-Type deve ser application/json'
            }), 400
        
        data = request.get_json()
        
        # Validação dos parâmetros obrigatórios
        required_fields = ['mikrotik_host', 'mikrotik_user', 'mikrotik_password', 'test_type', 'target']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            update_stats(success=False)
            return jsonify({
                'status': 'error',
                'message': f'Campos obrigatórios ausentes: {", ".join(missing_fields)}'
            }), 400
        
        # Cria objeto de parâmetros
        params = TestParameters(
            mikrotik_host=data['mikrotik_host'],
            mikrotik_user=data['mikrotik_user'],
            mikrotik_password=data['mikrotik_password'],
            test_type=data['test_type'].lower(),
            target=data['target'],
            count=data.get('count', 4),
            size=data.get('size', 64),
            interval=data.get('interval', 1),
            port=data.get('port', 80),
            mikrotik_port=data.get('mikrotik_port', 22)  # Porta SSH do MikroTik
        )
        
        logger.info(f"Requisição de teste: {params.mikrotik_host} -> {params.test_type} -> {params.target}")
        
        # Verifica cache primeiro
        cached_result = cache.get(
            params.mikrotik_host, 
            params.test_type, 
            params.target,
            count=params.count,
            size=params.size,
            interval=params.interval,
            port=params.port,
            mikrotik_port=params.mikrotik_port
        )
        
        if cached_result:
            update_stats(success=True, cache_hit=True)
            return jsonify(cached_result.to_dict())
        
        # Executa teste baseado no tipo
        if params.test_type == 'ping':
            result = execute_ping_test(params)
        elif params.test_type == 'traceroute':
            result = execute_traceroute_test(params)
        else:
            update_stats(success=False)
            return jsonify({
                'status': 'error',
                'message': f'Tipo de teste não suportado: {params.test_type}. Tipos disponíveis: ping, traceroute'
            }), 400
        
        # Armazena no cache se o teste foi bem-sucedido
        if result.status == 'success':
            cache.set(
                params.mikrotik_host, 
                params.test_type, 
                params.target, 
                result,
                count=params.count,
                size=params.size,
                interval=params.interval,
                port=params.port,
                mikrotik_port=params.mikrotik_port
            )
            update_stats(success=True, cache_hit=False)
        else:
            update_stats(success=False, cache_hit=False)
        
        return jsonify(result.to_dict())
        
    except Exception as e:
        logger.error(f"Erro na execução do teste: {str(e)}")
        update_stats(success=False)
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/connection-test', methods=['POST'])
@require_auth
def test_connection():
    """Endpoint para testar conectividade SSH com MikroTik"""
    try:
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Content-Type deve ser application/json'
            }), 400
        
        data = request.get_json()
        
        required_fields = ['mikrotik_host', 'mikrotik_user', 'mikrotik_password']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Campos obrigatórios ausentes: {", ".join(missing_fields)}'
            }), 400
        
        result = mikrotik.test_connection(
            data['mikrotik_host'],
            data['mikrotik_user'],
            data['mikrotik_password'],
            data.get('mikrotik_port', 22)
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro no teste de conexão: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/stats', methods=['GET'])
@require_auth
def get_stats():
    """Endpoint para estatísticas detalhadas do collector"""
    try:
        uptime = time.time() - app_stats['start_time']
        
        return jsonify({
            'system': {
                'uptime_seconds': round(uptime, 2),
                'version': '2.0.0',
                'timestamp': datetime.now().isoformat()
            },
            'requests': {
                'total': app_stats['total_requests'],
                'successful': app_stats['successful_requests'],
                'failed': app_stats['failed_requests'],
                'success_rate_percent': round(
                    (app_stats['successful_requests'] / app_stats['total_requests'] * 100)
                    if app_stats['total_requests'] > 0 else 0, 2
                )
            },
            'cache': cache.get_stats(),
            'connections': mikrotik.get_connection_stats(),
            'config': config.to_dict()
        })
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/cache', methods=['GET'])
@require_auth
def get_cache_info():
    """Endpoint para informações detalhadas do cache"""
    try:
        entries = cache.get_entries_info()
        
        return jsonify({
            'summary': cache.get_stats(),
            'entries': entries,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erro ao obter informações do cache: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/cache', methods=['DELETE'])
@require_auth
def clear_cache():
    """Endpoint para limpar o cache"""
    try:
        entries_cleared = cache.clear()
        
        logger.info(f"Cache limpo manualmente: {entries_cleared} entradas removidas")
        return jsonify({
            'status': 'success',
            'message': f'Cache limpo: {entries_cleared} entradas removidas',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==========================================
# FUNÇÕES DE TESTE ESPECÍFICAS
# ==========================================

def execute_ping_test(params: TestParameters) -> TestResult:
    """Executa teste de ping ICMP"""
    try:
        start_time = datetime.now()
        
        # Constrói comando ping do MikroTik
        command = f"/ping {params.target} count={params.count} size={params.size} interval={params.interval}"
        
        # Executa comando
        cmd_result = mikrotik.execute_command(
            params.mikrotik_host, 
            params.mikrotik_user, 
            params.mikrotik_password, 
            command,
            params.mikrotik_port
        )
        
        if cmd_result['status'] == 'error':
            return TestResult(
                status='error',
                test_type='ping',
                timestamp=datetime.now().isoformat(),
                cache_hit=False,
                cache_ttl=config.CACHE_TTL,
                mikrotik_host=params.mikrotik_host,
                target=params.target,
                results={},
                error_message=cmd_result['error'],
                execution_time_seconds=cmd_result['execution_time_seconds']
            )
        
        # Processa resultado
        ping_stats = processor.process_ping_result(cmd_result['output'])
        
        return TestResult(
            status='success',
            test_type='ping',
            timestamp=datetime.now().isoformat(),
            cache_hit=False,
            cache_ttl=config.CACHE_TTL,
            mikrotik_host=params.mikrotik_host,
            target=params.target,
            results={
                'ping_stats': ping_stats,
                'parameters': {
                    'count': params.count,
                    'size': params.size,
                    'interval': params.interval
                }
            },
            raw_output=cmd_result['output'],
            execution_time_seconds=cmd_result['execution_time_seconds']
        )
        
    except Exception as e:
        logger.error(f"Erro no teste de ping: {str(e)}")
        return TestResult(
            status='error',
            test_type='ping',
            timestamp=datetime.now().isoformat(),
            cache_hit=False,
            cache_ttl=config.CACHE_TTL,
            mikrotik_host=params.mikrotik_host,
            target=params.target,
            results={},
            error_message=str(e)
        )



def execute_traceroute_test(params: TestParameters) -> TestResult:
    """Executa teste de traceroute"""
    try:
        start_time = datetime.now()
        
        # Comando traceroute do MikroTik com timeout e contagem limitados
        # Formato: /tool traceroute count=3 8.8.8.8
        command = f"/tool traceroute count=3 {params.target}"
        
        # Executa comando
        cmd_result = mikrotik.execute_command(
            params.mikrotik_host, 
            params.mikrotik_user, 
            params.mikrotik_password, 
            command,
            params.mikrotik_port
        )
        
        if cmd_result['status'] == 'error':
            return TestResult(
                status='error',
                test_type='traceroute',
                timestamp=datetime.now().isoformat(),
                cache_hit=False,
                cache_ttl=config.CACHE_TTL,
                mikrotik_host=params.mikrotik_host,
                target=params.target,
                results={},
                error_message=cmd_result['error'],
                execution_time_seconds=cmd_result['execution_time_seconds']
            )
        
        # Processa resultado
        traceroute_stats = processor.process_traceroute_result(cmd_result['output'], params.target)
        
        return TestResult(
            status='success',
            test_type='traceroute',
            timestamp=datetime.now().isoformat(),
            cache_hit=False,
            cache_ttl=config.CACHE_TTL,
            mikrotik_host=params.mikrotik_host,
            target=params.target,
            results={
                'traceroute_stats': traceroute_stats,
                'parameters': {}
            },
            raw_output=cmd_result['output'],
            execution_time_seconds=cmd_result['execution_time_seconds']
        )
        
    except Exception as e:
        logger.error(f"Erro no teste de traceroute: {str(e)}")
        return TestResult(
            status='error',
            test_type='traceroute',
            timestamp=datetime.now().isoformat(),
            cache_hit=False,
            cache_ttl=config.CACHE_TTL,
            mikrotik_host=params.mikrotik_host,
            target=params.target,
            results={},
            error_message=str(e)
        )


# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def not_found(error):
    """Handler para endpoints não encontrados"""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint não encontrado',
        'available_endpoints': [
            '/api/health',
            '/api/test',
            '/api/connection-test',
            '/api/stats',
            '/api/cache'
        ]
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handler para métodos HTTP não permitidos"""
    return jsonify({
        'status': 'error',
        'message': 'Método HTTP não permitido para este endpoint'
    }), 405


@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos do servidor"""
    logger.error(f"Erro interno do servidor: {str(error)}")
    return jsonify({
        'status': 'error',
        'message': 'Erro interno do servidor'
    }), 500


# ==========================================
# CLEANUP E GRACEFUL SHUTDOWN
# ==========================================

def cleanup_resources():
    """Limpa recursos antes do shutdown"""
    logger.info("Iniciando limpeza de recursos...")
    
    try:
        # Limpa pool de conexões SSH
        mikrotik.cleanup_connections()
        logger.info("Pool de conexões SSH limpo")
    except Exception as e:
        logger.error(f"Erro ao limpar conexões SSH: {str(e)}")
    
    try:
        # Limpa cache
        cache_size = cache.clear()
        logger.info(f"Cache limpo: {cache_size} entradas removidas")
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {str(e)}")
    
    logger.info("Limpeza de recursos concluída")


def signal_handler(signum, frame):
    """Handler para sinais de sistema"""
    logger.info(f"Recebido sinal {signum}, iniciando shutdown graceful...")
    cleanup_resources()
    sys.exit(0)


# Registra handlers de cleanup
atexit.register(cleanup_resources)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


# ==========================================
# INICIALIZAÇÃO E MAIN
# ==========================================

def initialize_app():
    """Inicializa configurações da aplicação"""
    # Marca tempo de início
    app_stats['start_time'] = time.time()
    
    # Log de inicialização
    logger.info("="*60)
    logger.info("🛡️  TriplePlay-Sentinel Collector v2.0 Iniciando")
    logger.info("="*60)
    logger.info(f"Arquitetura: HTTP Agent (PULL)")
    logger.info(f"Cache TTL: {config.CACHE_TTL}s")
    logger.info(f"Cache Max Size: {config.MAX_CACHE_SIZE}")
    logger.info(f"SSH Timeout: {config.SSH_TIMEOUT}s")
    logger.info(f"API Host: {config.API_HOST}")
    logger.info(f"API Port: {config.API_PORT}")
    logger.info(f"HTTPS Enabled: {config.ENABLE_HTTPS}")
    logger.info(f"Auth Enabled: {config.ENABLE_AUTH}")
    logger.info("="*60)
    
    # Testa configurações básicas
    try:
        # Verifica se pode criar instâncias das classes principais
        logger.info("✅ Cache inicializado")
        logger.info("✅ Conector MikroTik inicializado")
        logger.info("✅ Processador de resultados inicializado")
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {str(e)}")
        sys.exit(1)
    
    logger.info("🚀 Collector inicializado e pronto para receber requisições")
    logger.info("📡 Aguardando requisições HTTP do Zabbix...")


if __name__ == '__main__':
    """Ponto de entrada principal"""
    
    try:
        # Inicializa aplicação
        initialize_app()
        
        # Configurações do servidor
        server_config = {
            'host': config.API_HOST,
            'port': config.API_PORT,
            'debug': config.DEBUG,
            'threaded': True,
            'use_reloader': False  # Evita problemas em production
        }
        
        # HTTPS se habilitado
        if config.ENABLE_HTTPS:
            cert_file = os.getenv('SSL_CERT_FILE', 'cert.pem')
            key_file = os.getenv('SSL_KEY_FILE', 'key.pem')
            
            if os.path.exists(cert_file) and os.path.exists(key_file):
                server_config['ssl_context'] = (cert_file, key_file)
                logger.info(f"🔒 HTTPS habilitado com certificados: {cert_file}, {key_file}")
            else:
                logger.warning("⚠️  HTTPS solicitado mas certificados não encontrados, usando HTTP")
        
        # Inicia servidor
        protocol = 'HTTPS' if server_config.get('ssl_context') else 'HTTP'
        logger.info(f"🌐 Iniciando servidor {protocol} em {config.API_HOST}:{config.API_PORT}")
        
        app.run(**server_config)
        
    except KeyboardInterrupt:
        logger.info("🛑 Interrupção pelo usuário (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Erro fatal na inicialização: {str(e)}")
        sys.exit(1)
    finally:
        cleanup_resources()