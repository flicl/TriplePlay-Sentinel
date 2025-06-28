#!/usr/bin/env python3
"""
TriplePlay-Sentinel Collector - Versão API Pura
Sistema de Monitoramento Centralizado MikroTik-Zabbix via API MikroTik

Esta versão utiliza APENAS a API MikroTik para máxima performance e simplicidade.
SSH foi completamente removido.
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
from processor import processor

# Import do conector API puro (sem SSH)
from mikrotik_api_implementation import mikrotik

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE) if config.LOG_FILE else logging.NullHandler()
    ]
)
logger = logging.getLogger('sentinel-collector-api')

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
    'cache_misses': 0,
    'api_calls': 0,
    'batch_api_calls': 0
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


def update_stats(success: bool, cache_hit: bool = False, api_call: bool = True, batch_call: bool = False):
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
        
        if api_call:
            app_stats['api_calls'] += 1
        
        if batch_call:
            app_stats['batch_api_calls'] += 1


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
        'service': 'TriplePlay-Sentinel Collector API',
        'version': '3.0.0',
        'status': 'running',
        'description': 'Sistema de monitoramento centralizado MikroTik-Zabbix via API MikroTik pura',
        'architecture': 'API MikroTik (alta performance)',
        'connection_method': 'api_only',
        'endpoints': {
            'health': '/api/health',
            'test': '/api/test',
            'batch': '/api/batch',
            'stats': '/api/stats',
            'cache': '/api/cache',
            'connection_test': '/api/connection-test'
        },
        'supported_tests': ['ping', 'traceroute'],
        'performance': {
            'concurrent_connections': '50+',
            'avg_response_time': '<200ms',
            'batch_processing': 'native'
        },
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
            'version': '3.0.0',
            'connection_method': 'api_only',
            'uptime_seconds': round(uptime, 2),
            'cache': cache.get_stats(),
            'api_connections': mikrotik.get_connection_stats(),
            'requests': {
                'total': app_stats['total_requests'],
                'successful': app_stats['successful_requests'],
                'failed': app_stats['failed_requests'],
                'success_rate_percent': (
                    (app_stats['successful_requests'] / app_stats['total_requests'] * 100)
                    if app_stats['total_requests'] > 0 else 0
                ),
                'api_calls': app_stats['api_calls'],
                'batch_calls': app_stats['batch_api_calls']
            },
            'performance': {
                'cache_hit_rate': (
                    (app_stats['cache_hits'] / max(1, app_stats['cache_hits'] + app_stats['cache_misses']) * 100)
                ),
                'avg_response_time_ms': mikrotik.get_connection_stats()['performance']['avg_response_time_ms']
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
    Endpoint principal para execução de testes via API MikroTik
    
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
            update_stats(success=False, api_call=False)
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
            mikrotik_port=data.get('mikrotik_port', 8728)  # Porta API do MikroTik
        )
        
        logger.info(f"Requisição de teste API: {params.mikrotik_host} -> {params.test_type} -> {params.target}")
        
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
            update_stats(success=True, cache_hit=True, api_call=False)
            return jsonify(cached_result.to_dict())
        
        # Executa teste baseado no tipo via API
        if params.test_type == 'ping':
            result = execute_ping_test_api(params)
        elif params.test_type == 'traceroute':
            result = execute_traceroute_test_api(params)
        else:
            update_stats(success=False, api_call=False)
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
        update_stats(success=False, api_call=False)
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/batch', methods=['POST'])
@require_auth
def execute_batch_test():
    """
    Endpoint para execução de testes em batch (alta performance)
    
    Executa múltiplos testes simultaneamente via API MikroTik
    """
    try:
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Content-Type deve ser application/json'
            }), 400
        
        data = request.get_json()
        
        # Validação
        required_fields = ['mikrotik_host', 'mikrotik_user', 'mikrotik_password', 'test_type', 'targets']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Campos obrigatórios ausentes: {", ".join(missing_fields)}'
            }), 400
        
        targets = data['targets']
        if not isinstance(targets, list) or len(targets) == 0:
            return jsonify({
                'status': 'error',
                'message': 'Campo targets deve ser uma lista não vazia'
            }), 400
        
        if len(targets) > 100:
            return jsonify({
                'status': 'error',
                'message': 'Máximo de 100 targets por batch'
            }), 400
        
        logger.info(f"Requisição batch API: {data['mikrotik_host']} -> {len(targets)} targets")
        
        # Executa batch via API
        if data['test_type'].lower() == 'ping':
            batch_results = execute_batch_ping_api(
                data['mikrotik_host'],
                data['mikrotik_user'],
                data['mikrotik_password'],
                targets,
                data.get('count', 4),
                data.get('mikrotik_port', 8728)
            )
            
            update_stats(success=True, batch_call=True)
            
            return jsonify({
                'status': 'success',
                'batch_size': len(targets),
                'results': {target: result.to_dict() for target, result in batch_results.items()},
                'method': 'api_batch',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Batch não suportado para tipo: {data["test_type"]}'
            }), 400
        
    except Exception as e:
        logger.error(f"Erro no batch test: {str(e)}")
        update_stats(success=False, batch_call=True)
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/connection-test', methods=['POST'])
@require_auth
def test_connection():
    """Endpoint para testar conectividade API com MikroTik"""
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
        
        port = data.get('mikrotik_port', 8728)
        
        # Testa conexão API
        result = mikrotik.test_connection(
            data['mikrotik_host'],
            data['mikrotik_user'],
            data['mikrotik_password'],
            port
        )
        
        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 503
            
    except Exception as e:
        logger.error(f"Erro no teste de conexão: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


# ==========================================
# FUNÇÕES DE TESTE ESPECÍFICAS (API)
# ==========================================

def execute_ping_test_api(params: TestParameters) -> TestResult:
    """Executa teste de ping via API MikroTik"""
    try:
        # Comando ping via API
        command = f'/ping {params.target} count={params.count} size={params.size}'
        
        cmd_result = mikrotik.execute_command(
            params.mikrotik_host,
            params.mikrotik_user,
            params.mikrotik_password,
            command,
            params.mikrotik_port
        )
        
        if cmd_result['status'] == 'success':
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
                    },
                    'method': 'api'
                },
                raw_output=cmd_result['output'],
                execution_time_seconds=cmd_result['execution_time_seconds']
            )
        else:
            return TestResult(
                status='error',
                test_type='ping',
                timestamp=datetime.now().isoformat(),
                cache_hit=False,
                cache_ttl=config.CACHE_TTL,
                mikrotik_host=params.mikrotik_host,
                target=params.target,
                results={'error': cmd_result['error'], 'method': 'api'},
                raw_output=cmd_result.get('output', ''),
                execution_time_seconds=cmd_result['execution_time_seconds']
            )
            
    except Exception as e:
        logger.error(f"Erro no teste de ping API: {str(e)}")
        return TestResult(
            status='error',
            test_type='ping',
            timestamp=datetime.now().isoformat(),
            cache_hit=False,
            cache_ttl=config.CACHE_TTL,
            mikrotik_host=params.mikrotik_host,
            target=params.target,
            results={'error': str(e), 'method': 'api'},
            raw_output='',
            execution_time_seconds=0
        )


def execute_traceroute_test_api(params: TestParameters) -> TestResult:
    """Executa teste de traceroute via API MikroTik"""
    try:
        # Comando traceroute via API
        command = f'/tool traceroute {params.target} count={params.count}'
        
        cmd_result = mikrotik.execute_command(
            params.mikrotik_host,
            params.mikrotik_user,
            params.mikrotik_password,
            command,
            params.mikrotik_port
        )
        
        if cmd_result['status'] == 'success':
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
                    'parameters': {
                        'count': params.count
                    },
                    'method': 'api'
                },
                raw_output=cmd_result['output'],
                execution_time_seconds=cmd_result['execution_time_seconds']
            )
        else:
            return TestResult(
                status='error',
                test_type='traceroute',
                timestamp=datetime.now().isoformat(),
                cache_hit=False,
                cache_ttl=config.CACHE_TTL,
                mikrotik_host=params.mikrotik_host,
                target=params.target,
                results={'error': cmd_result['error'], 'method': 'api'},
                raw_output=cmd_result.get('output', ''),
                execution_time_seconds=cmd_result['execution_time_seconds']
            )
            
    except Exception as e:
        logger.error(f"Erro no teste de traceroute API: {str(e)}")
        return TestResult(
            status='error',
            test_type='traceroute',
            timestamp=datetime.now().isoformat(),
            cache_hit=False,
            cache_ttl=config.CACHE_TTL,
            mikrotik_host=params.mikrotik_host,
            target=params.target,
            results={'error': str(e), 'method': 'api'},
            raw_output='',
            execution_time_seconds=0
        )


def execute_batch_ping_api(host: str, username: str, password: str, targets: list, count: int = 4, port: int = 8728) -> Dict[str, TestResult]:
    """Executa múltiplos pings simultaneamente via API"""
    try:
        # Executa batch via API
        batch_results = mikrotik.execute_batch_ping(host, username, password, targets, count, port)
        
        # Converte para TestResult
        final_results = {}
        
        for target, result in batch_results.items():
            if result['status'] == 'success':
                ping_stats = processor.process_ping_result(result['output'])
                
                final_results[target] = TestResult(
                    status='success',
                    test_type='ping',
                    timestamp=datetime.now().isoformat(),
                    cache_hit=False,
                    cache_ttl=config.CACHE_TTL,
                    mikrotik_host=host,
                    target=target,
                    results={
                        'ping_stats': ping_stats,
                        'method': 'api_batch'
                    },
                    raw_output=result['output'],
                    execution_time_seconds=result['execution_time_seconds']
                )
            else:
                final_results[target] = TestResult(
                    status='error',
                    test_type='ping',
                    timestamp=datetime.now().isoformat(),
                    cache_hit=False,
                    cache_ttl=config.CACHE_TTL,
                    mikrotik_host=host,
                    target=target,
                    results={'error': result['error'], 'method': 'api_batch'},
                    raw_output='',
                    execution_time_seconds=result['execution_time_seconds']
                )
        
        return final_results
        
    except Exception as e:
        logger.error(f"Erro no batch ping API: {str(e)}")
        
        # Retorna erro para todos os targets
        error_result = TestResult(
            status='error',
            test_type='ping',
            timestamp=datetime.now().isoformat(),
            cache_hit=False,
            cache_ttl=config.CACHE_TTL,
            mikrotik_host=host,
            target='batch',
            results={'error': str(e), 'method': 'api_batch'},
            raw_output='',
            execution_time_seconds=0
        )
        
        return {target: error_result for target in targets}


# ==========================================
# ENDPOINTS DE ESTATÍSTICAS E CACHE
# ==========================================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Endpoint para estatísticas do sistema"""
    try:
        uptime = time.time() - app_stats['start_time']
        
        return jsonify({
            'system': {
                'uptime_seconds': round(uptime, 2),
                'version': '3.0.0',
                'connection_method': 'api_only'
            },
            'requests': app_stats.copy(),
            'cache': cache.get_stats(),
            'api_connections': mikrotik.get_connection_stats(),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/cache', methods=['GET', 'DELETE'])
def cache_management():
    """Endpoint para gerenciamento do cache"""
    try:
        if request.method == 'GET':
            return jsonify({
                'cache_stats': cache.get_stats(),
                'timestamp': datetime.now().isoformat()
            })
        elif request.method == 'DELETE':
            cleared_count = cache.clear()
            return jsonify({
                'status': 'success',
                'message': f'Cache limpo: {cleared_count} entradas removidas',
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Erro no gerenciamento do cache: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


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
            '/api/health', '/api/test', '/api/batch', 
            '/api/stats', '/api/cache', '/api/connection-test'
        ]
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handler para métodos HTTP não permitidos"""
    return jsonify({
        'status': 'error',
        'message': f'Método {request.method} não permitido para este endpoint'
    }), 405


@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos do servidor"""
    logger.error(f"Erro interno do servidor: {str(error)}")
    return jsonify({
        'status': 'error',
        'message': 'Erro interno do servidor',
        'timestamp': datetime.now().isoformat()
    }), 500


# ==========================================
# CLEANUP E GRACEFUL SHUTDOWN
# ==========================================

def cleanup_resources():
    """Limpa recursos antes do shutdown"""
    try:
        logger.info("🧹 Limpando recursos...")
        
        # Limpa conexões API
        mikrotik.cleanup_connections()
        logger.info("✅ Conexões API limpas")
        
        # Estatísticas finais
        uptime = time.time() - app_stats['start_time']
        logger.info(f"📊 Estatísticas finais:")
        logger.info(f"   - Uptime: {uptime:.1f}s")
        logger.info(f"   - Total requests: {app_stats['total_requests']}")
        logger.info(f"   - API calls: {app_stats['api_calls']}")
        logger.info(f"   - Batch calls: {app_stats['batch_api_calls']}")
        logger.info(f"   - Success rate: {(app_stats['successful_requests']/max(1,app_stats['total_requests'])*100):.1f}%")
        
        logger.info("✅ Cleanup concluído")
        
    except Exception as e:
        logger.error(f"Erro durante cleanup: {str(e)}")


def signal_handler(signum, frame):
    """Handler para sinais de sistema"""
    logger.info(f"🛑 Sinal {signum} recebido, iniciando shutdown graceful...")
    cleanup_resources()
    sys.exit(0)


# Registra handlers de cleanup
atexit.register(cleanup_resources)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def initialize_app():
    """Inicializa a aplicação"""
    logger.info("🚀 Inicializando TriplePlay-Sentinel Collector API")
    logger.info(f"📡 Versão: 3.0.0 (API MikroTik Pura)")
    logger.info(f"🔌 Método de conexão: API apenas (sem SSH)")
    logger.info(f"⚡ Pool de conexões API: {mikrotik.api_pool.max_connections} máximo")
    logger.info(f"💾 Cache TTL: {config.CACHE_TTL}s")
    logger.info(f"🏃 Workers: {config.MAX_WORKERS}")
    
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
