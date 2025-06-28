#!/usr/bin/env python3
"""
Integração da API MikroTik no sistema TriplePlay-Sentinel existente
Versão híbrida: API como padrão, SSH como fallback
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, List
from mikrotik_api_implementation import api_pool, execute_api_ping, execute_api_batch_ping

logger = logging.getLogger('sentinel-hybrid')


class HybridMikroTikConnector:
    """Conector híbrido: API MikroTik + SSH fallback para máxima confiabilidade"""
    
    def __init__(self):
        # Configurações
        self.use_api = os.getenv('USE_MIKROTIK_API', 'true').lower() == 'true'
        self.api_timeout = int(os.getenv('API_TIMEOUT', '10'))
        self.ssh_fallback = os.getenv('SSH_FALLBACK', 'true').lower() == 'true'
        
        # Estatísticas
        self.stats = {
            'api_success': 0,
            'api_failures': 0, 
            'ssh_fallback_used': 0,
            'total_requests': 0,
            'avg_api_time': 0.0,
            'avg_ssh_time': 0.0
        }
        
        # Import do conector SSH existente
        from mikrotik import mikrotik as ssh_connector
        self.ssh_connector = ssh_connector
    
    def execute_command(self, host: str, username: str, password: str, command: str, port: int = 22) -> Dict[str, Any]:
        """
        Interface unificada: tenta API primeiro, SSH como fallback
        Mantém compatibilidade com o sistema existente
        """
        self.stats['total_requests'] += 1
        start_time = time.time()
        
        # Detecta tipo de comando para escolher método otimizado
        if self.use_api and '/ping' in command:
            try:
                # Extrai parâmetros do comando ping SSH
                ping_params = self._parse_ping_command(command)
                
                # Executa via API (muito mais rápido)
                api_start = time.time()
                result = execute_api_ping(
                    host, username, password,
                    ping_params['address'],
                    ping_params.get('count', 4)
                )
                api_time = time.time() - api_start
                
                if result['status'] == 'success':
                    self.stats['api_success'] += 1
                    self.stats['avg_api_time'] = (
                        (self.stats['avg_api_time'] * (self.stats['api_success'] - 1) + api_time) 
                        / self.stats['api_success']
                    )
                    
                    # Converte resultado API para formato SSH compatível
                    return self._convert_api_result_to_ssh_format(result, api_time)
                else:
                    raise Exception(f"API error: {result.get('error', 'Unknown')}")
                    
            except Exception as e:
                logger.warning(f"API falhou para {host}, usando SSH fallback: {e}")
                self.stats['api_failures'] += 1
                
                if not self.ssh_fallback:
                    return {
                        'status': 'error',
                        'error': f'API failed and SSH fallback disabled: {str(e)}',
                        'execution_time_seconds': time.time() - start_time
                    }
        
        # Fallback para SSH ou comando não-ping
        if self.ssh_fallback or not self.use_api:
            try:
                ssh_start = time.time()
                self.stats['ssh_fallback_used'] += 1
                
                result = self.ssh_connector.execute_command(host, username, password, command, port)
                
                ssh_time = time.time() - ssh_start
                fallback_count = self.stats['ssh_fallback_used']
                self.stats['avg_ssh_time'] = (
                    (self.stats['avg_ssh_time'] * (fallback_count - 1) + ssh_time) 
                    / fallback_count
                )
                
                return result
                
            except Exception as e:
                return {
                    'status': 'error',
                    'error': f'Both API and SSH failed: {str(e)}',
                    'execution_time_seconds': time.time() - start_time
                }
        
        return {
            'status': 'error',
            'error': 'No execution method available',
            'execution_time_seconds': time.time() - start_time
        }
    
    def execute_batch_ping(self, host: str, username: str, password: str, targets: List[str], count: int = 4) -> Dict[str, Dict[str, Any]]:
        """
        Método especializado para múltiplos pings simultâneos
        Usa API para máxima performance em cenários de alta concorrência
        """
        if not self.use_api:
            return self._execute_batch_ping_ssh(host, username, password, targets, count)
        
        try:
            start_time = time.time()
            
            # Executa batch via API (todos simultaneamente)
            batch_results = execute_api_batch_ping(host, username, password, targets, count)
            
            execution_time = time.time() - start_time
            logger.info(f"Batch API ping: {len(targets)} targets em {execution_time:.2f}s")
            
            # Converte resultados para formato padrão
            converted_results = {}
            for target, result in batch_results.items():
                converted_results[target] = self._convert_api_result_to_ssh_format(result, execution_time / len(targets))
            
            return converted_results
            
        except Exception as e:
            logger.error(f"Batch API falhou: {e}")
            
            if self.ssh_fallback:
                return self._execute_batch_ping_ssh(host, username, password, targets, count)
            else:
                # Retorna erro para todos os targets
                error_result = {
                    'status': 'error',
                    'error': str(e),
                    'execution_time_seconds': 0
                }
                return {target: error_result for target in targets}
    
    def _execute_batch_ping_ssh(self, host: str, username: str, password: str, targets: List[str], count: int = 4) -> Dict[str, Dict[str, Any]]:
        """Executa batch ping via SSH (método tradicional)"""
        results = {}
        
        for target in targets:
            command = f'/ping {target} count={count}'
            results[target] = self.ssh_connector.execute_command(host, username, password, command)
        
        return results
    
    def _parse_ping_command(self, command: str) -> Dict[str, Any]:
        """Extrai parâmetros do comando ping SSH"""
        parts = command.split()
        params = {'address': None, 'count': 4, 'size': 64}
        
        for i, part in enumerate(parts):
            if part == '/ping' and i + 1 < len(parts):
                params['address'] = parts[i + 1]
            elif part.startswith('count='):
                params['count'] = int(part.split('=')[1])
            elif part.startswith('size='):
                params['size'] = int(part.split('=')[1])
        
        return params
    
    def _convert_api_result_to_ssh_format(self, api_result: Dict[str, Any], execution_time: float) -> Dict[str, Any]:
        """Converte resultado da API para formato compatível com SSH"""
        
        if api_result['status'] == 'success':
            ping_stats = api_result['results']['ping_stats']
            
            # Simula output SSH para manter compatibilidade
            ssh_output = self._generate_ssh_like_output(ping_stats)
            
            return {
                'status': 'success',
                'output': ssh_output,
                'error': '',
                'exit_status': 0,
                'execution_time_seconds': execution_time,
                'timestamp': datetime.now().isoformat(),
                'method': 'api'  # Identifica que veio da API
            }
        else:
            return {
                'status': 'error',
                'output': '',
                'error': api_result.get('error', 'API error'),
                'exit_status': 1,
                'execution_time_seconds': execution_time,
                'timestamp': datetime.now().isoformat(),
                'method': 'api'
            }
    
    def _generate_ssh_like_output(self, ping_stats: Dict[str, Any]) -> str:
        """Gera output no formato SSH para compatibilidade com parser existente"""
        
        # Formato similar ao output SSH do MikroTik
        output_lines = []
        
        # Simula linhas individuais de ping
        for i in range(ping_stats['packets_sent']):
            if i < ping_stats['packets_received']:
                time_ms = ping_stats['avg_time_ms']  # Simplificado
                output_lines.append(f"64 byte ping: ttl=64 time={time_ms}ms")
            else:
                output_lines.append("timeout")
        
        # Linha de estatísticas (formato MikroTik)
        stats_line = (
            f"sent={ping_stats['packets_sent']} "
            f"received={ping_stats['packets_received']} "
            f"packet-loss={ping_stats['packet_loss_percent']:.0f}% "
            f"min-rtt={ping_stats.get('min_time_ms', 0):.0f}ms "
            f"avg-rtt={ping_stats.get('avg_time_ms', 0):.0f}ms "
            f"max-rtt={ping_stats.get('max_time_ms', 0):.0f}ms"
        )
        output_lines.append(stats_line)
        
        return '\n'.join(output_lines)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas combinadas (API + SSH)"""
        
        # Stats do SSH existente
        ssh_stats = self.ssh_connector.get_connection_stats()
        
        # Stats da API
        api_stats = api_pool.get_stats()
        
        # Stats combinadas
        return {
            'api': {
                'enabled': self.use_api,
                'success_rate': (
                    (self.stats['api_success'] / max(1, self.stats['api_success'] + self.stats['api_failures'])) * 100
                ),
                'avg_response_time_ms': self.stats['avg_api_time'] * 1000,
                'pool_stats': api_stats,
                'total_calls': self.stats['api_success'] + self.stats['api_failures']
            },
            'ssh': {
                'fallback_used': self.stats['ssh_fallback_used'],
                'avg_response_time_ms': self.stats['avg_ssh_time'] * 1000,
                'connection_stats': ssh_stats
            },
            'hybrid': {
                'total_requests': self.stats['total_requests'],
                'api_success_rate': (self.stats['api_success'] / max(1, self.stats['total_requests'])) * 100,
                'fallback_rate': (self.stats['ssh_fallback_used'] / max(1, self.stats['total_requests'])) * 100,
                'performance_improvement': (
                    self.stats['avg_ssh_time'] / max(0.001, self.stats['avg_api_time'])
                ) if self.stats['avg_api_time'] > 0 else 1
            }
        }
    
    def test_connection(self, host: str, username: str, password: str, port: int = 22) -> Dict[str, Any]:
        """Testa conectividade (API primeiro, SSH fallback)"""
        
        results = {'api': None, 'ssh': None}
        
        # Testa API se habilitada
        if self.use_api:
            try:
                api_start = time.time()
                api_result = execute_api_ping(host, username, password, '8.8.8.8', 1)
                api_time = time.time() - api_start
                
                results['api'] = {
                    'status': api_result['status'],
                    'response_time_ms': api_time * 1000,
                    'method': 'api'
                }
            except Exception as e:
                results['api'] = {
                    'status': 'error',
                    'error': str(e),
                    'method': 'api'
                }
        
        # Testa SSH se API falhou ou como fallback
        if not results['api'] or results['api']['status'] != 'success':
            try:
                ssh_result = self.ssh_connector.test_connection(host, username, password, port)
                results['ssh'] = ssh_result
            except Exception as e:
                results['ssh'] = {
                    'status': 'error',
                    'error': str(e),
                    'method': 'ssh'
                }
        
        # Determina resultado final
        if results['api'] and results['api']['status'] == 'success':
            return {
                'status': 'success',
                'message': 'API connection successful',
                'methods': results,
                'recommended': 'api'
            }
        elif results['ssh'] and results['ssh']['status'] == 'success':
            return {
                'status': 'success',
                'message': 'SSH connection successful (API failed)',
                'methods': results,
                'recommended': 'ssh'
            }
        else:
            return {
                'status': 'error',
                'message': 'Both API and SSH connections failed',
                'methods': results,
                'recommended': 'none'
            }


# Substituição do conector existente
hybrid_mikrotik = HybridMikroTikConnector()


# Exemplo de uso no app.py
def execute_ping_test_optimized(params) -> 'TestResult':
    """Versão otimizada do execute_ping_test usando API"""
    
    try:
        # Usa o conector híbrido (API + SSH fallback)
        cmd_result = hybrid_mikrotik.execute_command(
            params.mikrotik_host,
            params.mikrotik_user,
            params.mikrotik_password,
            f'/ping {params.target} count={params.count} size={params.size}'
        )
        
        if cmd_result['status'] == 'success':
            # Processa resultado normalmente (compatível com parser existente)
            from processor import processor
            ping_stats = processor.process_ping_result(cmd_result['output'])
            
            from models import TestResult
            return TestResult(
                status='success',
                test_type='ping',
                timestamp=datetime.now().isoformat(),
                cache_hit=False,
                mikrotik_host=params.mikrotik_host,
                target=params.target,
                results={
                    'ping_stats': ping_stats,
                    'parameters': {
                        'count': params.count,
                        'size': params.size,
                        'interval': params.interval
                    },
                    'method': cmd_result.get('method', 'ssh')  # Identifica método usado
                },
                raw_output=cmd_result['output'],
                execution_time_seconds=cmd_result['execution_time_seconds']
            )
        else:
            from models import TestResult
            return TestResult(
                status='error',
                test_type='ping',
                timestamp=datetime.now().isoformat(),
                cache_hit=False,
                mikrotik_host=params.mikrotik_host,
                target=params.target,
                results={'error': cmd_result['error']},
                raw_output=cmd_result.get('output', ''),
                execution_time_seconds=cmd_result['execution_time_seconds']
            )
            
    except Exception as e:
        logger.error(f"Erro no teste de ping otimizado: {str(e)}")
        from models import TestResult
        return TestResult(
            status='error',
            test_type='ping',
            timestamp=datetime.now().isoformat(),
            cache_hit=False,
            mikrotik_host=params.mikrotik_host,
            target=params.target,
            results={'error': str(e)},
            raw_output='',
            execution_time_seconds=0
        )


# Endpoint para batch requests (novo)
def execute_batch_ping_test(mikrotik_host: str, targets: List[str], username: str, password: str, count: int = 4) -> Dict[str, 'TestResult']:
    """Executa múltiplos pings otimizados via API"""
    
    try:
        # Executa batch via API (muito mais rápido)
        batch_results = hybrid_mikrotik.execute_batch_ping(mikrotik_host, username, password, targets, count)
        
        # Converte para TestResult
        from models import TestResult
        final_results = {}
        
        for target, result in batch_results.items():
            if result['status'] == 'success':
                from processor import processor
                ping_stats = processor.process_ping_result(result['output'])
                
                final_results[target] = TestResult(
                    status='success',
                    test_type='ping',
                    timestamp=datetime.now().isoformat(),
                    cache_hit=False,
                    mikrotik_host=mikrotik_host,
                    target=target,
                    results={
                        'ping_stats': ping_stats,
                        'method': result.get('method', 'batch_api')
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
                    mikrotik_host=mikrotik_host,
                    target=target,
                    results={'error': result['error']},
                    raw_output='',
                    execution_time_seconds=result['execution_time_seconds']
                )
        
        return final_results
        
    except Exception as e:
        logger.error(f"Erro no batch ping test: {str(e)}")
        
        # Retorna erro para todos os targets
        from models import TestResult
        error_result = TestResult(
            status='error',
            test_type='ping',
            timestamp=datetime.now().isoformat(),
            cache_hit=False,
            mikrotik_host=mikrotik_host,
            target='batch',
            results={'error': str(e)},
            raw_output='',
            execution_time_seconds=0
        )
        
        return {target: error_result for target in targets}


if __name__ == "__main__":
    # Teste de performance híbrido
    
    print("=== Teste do Conector Híbrido ===")
    
    mikrotik_host = "192.168.1.1"
    username = "admin"
    password = "password"
    
    # 1. Teste de conectividade
    print("1. Testando conectividade...")
    conn_test = hybrid_mikrotik.test_connection(mikrotik_host, username, password)
    print(f"Resultado: {conn_test['status']} - {conn_test['message']}")
    print(f"Método recomendado: {conn_test['recommended']}")
    
    # 2. Teste individual (API vs SSH)
    print("\n2. Teste individual...")
    start_time = time.time()
    single_result = hybrid_mikrotik.execute_command(mikrotik_host, username, password, '/ping 8.8.8.8 count=4')
    single_time = time.time() - start_time
    print(f"Ping individual: {single_time:.2f}s - Método: {single_result.get('method', 'ssh')}")
    
    # 3. Teste batch (alta concorrência)
    print("\n3. Teste batch (10 targets)...")
    targets = ['8.8.8.8', '1.1.1.1', '8.8.4.4', '9.9.9.9', '208.67.222.222',
               '1.0.0.1', '8.26.56.26', '9.9.9.10', '149.112.112.112', '76.76.19.19']
    
    start_time = time.time()
    batch_results = hybrid_mikrotik.execute_batch_ping(mikrotik_host, username, password, targets, 4)
    batch_time = time.time() - start_time
    
    successful = sum(1 for r in batch_results.values() if r['status'] == 'success')
    print(f"Batch ping: {len(targets)} targets em {batch_time:.2f}s")
    print(f"Sucessos: {successful}/{len(targets)}")
    print(f"Performance: {len(targets)/batch_time:.1f} targets/segundo")
    
    # 4. Estatísticas finais
    print("\n4. Estatísticas do conector:")
    stats = hybrid_mikrotik.get_connection_stats()
    print(f"API success rate: {stats['api']['success_rate']:.1f}%")
    print(f"SSH fallback rate: {stats['hybrid']['fallback_rate']:.1f}%")
    print(f"Performance improvement: {stats['hybrid']['performance_improvement']:.1f}x")
