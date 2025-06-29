#!/usr/bin/env python3
"""
TriplePlay-Sentinel - Async MikroTik Connector (OTIMIZADO)
Sistema otimizado para alta concorrência (1000-2000 requisições simultâneas)
"""

import asyncio
import aiohttp
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor
import librouteros
from sentinel_config import config

logger = logging.getLogger('sentinel-mikrotik-async')


@dataclass
class MikroTikConnectionInfo:
    """Informações de conexão MikroTik"""
    host: str
    username: str
    password: str
    port: int = 8728
    use_ssl: bool = False


class AsyncMikroTikConnector:
    """Conector MikroTik otimizado para alta concorrência usando async/await"""
    
    def __init__(self):
        self.connection_pools = {}  # Pool por host
        self.semaphores = {}        # Semáforos por host para controlar concorrência
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'active_connections': 0,
            'peak_connections': 0
        }
        self.stats_lock = threading.Lock()
        
        # Thread pool para operações síncronas (librouteros)
        self.thread_pool = ThreadPoolExecutor(
            max_workers=config.MAX_WORKERS,
            thread_name_prefix='mikrotik-sync'
        )
    
    def _get_host_key(self, host: str, username: str, port: int) -> str:
        """Gera chave única para o host"""
        return f"{host}:{port}:{username}"
    
    def _get_semaphore(self, host_key: str) -> asyncio.Semaphore:
        """Obtém semáforo para controlar concorrência por host"""
        if host_key not in self.semaphores:
            self.semaphores[host_key] = asyncio.Semaphore(config.MAX_CONCURRENT_COMMANDS)
        return self.semaphores[host_key]
    
    async def _execute_sync_operation(self, operation, *args, **kwargs):
        """Executa operação síncrona em thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, operation, *args, **kwargs)
    
    def _sync_ping_operation(self, conn_info: MikroTikConnectionInfo, target: str, count: int) -> Dict[str, Any]:
        """Operação de ping síncrona usando librouteros"""
        try:
            # Conecta (reutiliza conexão se possível)
            connection = librouteros.connect(
                host=conn_info.host,
                username=conn_info.username,
                password=conn_info.password,
                port=conn_info.port,
                timeout=config.MIKROTIK_API_TIMEOUT
            )
            
            # Executa ping
            start_time = time.time()
            ping_responses = connection.path('ping').query(
                address=target,
                count=str(count)
            )
            
            # Processa resultados
            results = []
            for response in ping_responses:
                results.append(response)
            
            connection.close()
            execution_time = time.time() - start_time
            
            # Processa estatísticas
            return self._process_ping_results(results, execution_time, target)
            
        except Exception as e:
            logger.error(f"Erro no ping {conn_info.host} -> {target}: {e}")
            return {
                'target': target,
                'status': 'error',
                'error': str(e),
                'packets_sent': 0,
                'packets_received': 0,
                'packet_loss_percent': 100.0,
                'execution_time_seconds': 0
            }
    
    def _process_ping_results(self, results: List[Dict], execution_time: float, target: str) -> Dict[str, Any]:
        """Processa resultados do ping"""
        if not results:
            return {
                'target': target,
                'status': 'error',
                'error': 'No ping results',
                'packets_sent': 0,
                'packets_received': 0,
                'packet_loss_percent': 100.0,
                'execution_time_seconds': execution_time
            }
        
        times = []
        sent = 0
        received = 0
        
        for result in results:
            sent += 1
            if 'time' in result and 'timeout' not in result:
                received += 1
                # Processa tempo
                time_str = str(result['time'])
                try:
                    time_val = float(time_str.replace('ms', '').replace('us', '').replace('s', ''))
                    if 'us' in time_str:
                        time_val = time_val / 1000
                    elif 's' in time_str and 'ms' not in time_str:
                        time_val = time_val * 1000
                    times.append(time_val)
                except ValueError:
                    pass
        
        packet_loss = ((sent - received) / sent * 100) if sent > 0 else 100
        
        return {
            'target': target,
            'status': 'success',
            'packets_sent': sent,
            'packets_received': received,
            'packet_loss_percent': round(packet_loss, 2),
            'availability_percent': round(100 - packet_loss, 2),
            'min_time_ms': round(min(times), 2) if times else 0,
            'avg_time_ms': round(sum(times) / len(times), 2) if times else 0,
            'max_time_ms': round(max(times), 2) if times else 0,
            'jitter_ms': round(max(times) - min(times), 2) if len(times) > 1 else 0,
            'execution_time_seconds': round(execution_time, 2)
        }
    
    async def execute_single_ping(self, host: str, username: str, password: str, 
                                  target: str, count: int = 4, port: int = 8728) -> Dict[str, Any]:
        """Executa ping único de forma assíncrona"""
        host_key = self._get_host_key(host, username, port)
        semaphore = self._get_semaphore(host_key)
        
        async with semaphore:  # Controla concorrência por host
            with self.stats_lock:
                self.stats['total_requests'] += 1
                self.stats['active_connections'] += 1
                if self.stats['active_connections'] > self.stats['peak_connections']:
                    self.stats['peak_connections'] = self.stats['active_connections']
            
            try:
                conn_info = MikroTikConnectionInfo(host, username, password, port)
                result = await self._execute_sync_operation(
                    self._sync_ping_operation, conn_info, target, count
                )
                
                with self.stats_lock:
                    self.stats['successful_requests'] += 1
                
                return result
                
            except Exception as e:
                with self.stats_lock:
                    self.stats['failed_requests'] += 1
                
                logger.error(f"Erro no ping assíncrono {host} -> {target}: {e}")
                return {
                    'target': target,
                    'status': 'error',
                    'error': str(e),
                    'execution_time_seconds': 0
                }
            finally:
                with self.stats_lock:
                    self.stats['active_connections'] -= 1
    
    async def execute_batch_ping(self, host: str, username: str, password: str, 
                                 targets: List[str], count: int = 4, port: int = 8728) -> List[Dict[str, Any]]:
        """Executa múltiplos pings SIMULTANEAMENTE"""
        start_time = time.time()
        
        # Cria tasks para todos os pings simultaneamente
        tasks = []
        for target in targets:
            task = self.execute_single_ping(host, username, password, target, count, port)
            tasks.append(task)
        
        # Executa TODOS os pings em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa exceções
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'target': targets[i],
                    'status': 'error',
                    'error': str(result),
                    'execution_time_seconds': 0
                })
            else:
                processed_results.append(result)
        
        total_time = time.time() - start_time
        logger.info(f"Batch ping {host}: {len(targets)} targets em {total_time:.2f}s (paralelismo total)")
        
        return processed_results
    
    async def execute_multiple_hosts(self, hosts_config: List[Dict], command: str, 
                                     parameters: Dict = None, max_concurrent_hosts: int = None) -> Dict[str, Any]:
        """Executa comando em múltiplos hosts simultaneamente"""
        if max_concurrent_hosts is None:
            max_concurrent_hosts = config.MAX_CONCURRENT_HOSTS
        
        # Semáforo para controlar hosts simultâneos
        host_semaphore = asyncio.Semaphore(max_concurrent_hosts)
        
        async def execute_single_host(host_config):
            async with host_semaphore:
                # Implementar comando específico aqui
                # Por enquanto, só ping é implementado
                if command == 'ping' and parameters and 'targets' in parameters:
                    return await self.execute_batch_ping(
                        host_config['host'],
                        host_config['username'],
                        host_config['password'],
                        parameters['targets'],
                        parameters.get('count', 4),
                        host_config.get('port', 8728)
                    )
                else:
                    return {'error': f'Comando {command} não implementado'}
        
        # Executa em todos os hosts simultaneamente
        tasks = [execute_single_host(host_config) for host_config in hosts_config]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Organiza resultados por host
        host_results = {}
        for i, result in enumerate(results):
            host_key = f"{hosts_config[i]['host']}:{hosts_config[i].get('port', 8728)}"
            if isinstance(result, Exception):
                host_results[host_key] = {'error': str(result)}
            else:
                host_results[host_key] = result
        
        return host_results
    
    async def test_connection(self, host: str, username: str, password: str, 
                             port: int = 8728, use_ssl: bool = False) -> Dict[str, Any]:
        """Testa conectividade com MikroTik"""
        try:
            conn_info = MikroTikConnectionInfo(host, username, password, port, use_ssl)
            
            # Teste simples: obter identidade do sistema
            def sync_test():
                connection = librouteros.connect(
                    host=host, username=username, password=password, 
                    port=port, timeout=10
                )
                identity = list(connection.path('system', 'identity').query())[0]
                connection.close()
                return identity
            
            start_time = time.time()
            identity = await self._execute_sync_operation(sync_test)
            execution_time = time.time() - start_time
            
            return {
                'status': 'success',
                'host': host,
                'port': port,
                'identity': identity.get('name', 'Unknown'),
                'execution_time_seconds': round(execution_time, 2)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'host': host,
                'port': port,
                'error': str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do conector"""
        with self.stats_lock:
            success_rate = 0
            if self.stats['total_requests'] > 0:
                success_rate = (self.stats['successful_requests'] / self.stats['total_requests'] * 100)
            
            return {
                'total_requests': self.stats['total_requests'],
                'successful_requests': self.stats['successful_requests'],
                'failed_requests': self.stats['failed_requests'],
                'active_connections': self.stats['active_connections'],
                'peak_connections': self.stats['peak_connections'],
                'success_rate_percent': round(success_rate, 2),
                'semaphores': {
                    host_key: sem._value for host_key, sem in self.semaphores.items()
                },
                'max_concurrent_commands_per_host': config.MAX_CONCURRENT_COMMANDS,
                'max_concurrent_hosts': config.MAX_CONCURRENT_HOSTS
            }
    
    async def close_all_connections(self):
        """Fecha todas as conexões e limpa recursos"""
        # Fecha thread pool
        self.thread_pool.shutdown(wait=True)
        
        # Limpa semáforos
        self.semaphores.clear()
        
        logger.info("Todas as conexões MikroTik foram fechadas")


# Instância global do conector assíncrono
mikrotik_connector = AsyncMikroTikConnector()
