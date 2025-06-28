#!/usr/bin/env python3
"""
TriplePlay-Sentinel - Conector MikroTik API-Only
Sistema de Monitoramento 100% baseado na API MikroTik (sem SSH)
Otimizado para máxima performance e concorrência
"""

import time
import threading
import logging
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import hashlib
import ssl

logger = logging.getLogger('sentinel-mikrotik-api')


class MikroTikAPIConnector:
    """
    Conector 100% API MikroTik - Zero dependência SSH
    Otimizado para alta concorrência e performance
    """
    
    def __init__(self, max_connections_per_host: int = 20):
        self.connection_pools: Dict[str, aiohttp.TCPConnector] = {}
        self.sessions: Dict[str, aiohttp.ClientSession] = {}
        self.connection_lock = threading.RLock()
        self.max_connections_per_host = max_connections_per_host
        
        # Estatísticas de performance
        self._stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'concurrent_requests': 0,
            'avg_response_time': 0.0,
            'total_response_time': 0.0
        }
        
        # Pool de threads para operações síncronas
        self.thread_pool = ThreadPoolExecutor(max_workers=50)
        
        # Cache inteligente para respostas frequentes
        self.response_cache: Dict[str, Dict] = {}
        self.cache_ttl = 30  # segundos
        
    async def _get_session(self, host: str, port: int = 8728, use_ssl: bool = True) -> aiohttp.ClientSession:
        """Obtém sessão HTTP otimizada para o host"""
        session_key = f"{host}:{port}:{use_ssl}"
        
        if session_key not in self.sessions:
            # Configurações SSL otimizadas
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Connector com pool de conexões
            connector = aiohttp.TCPConnector(
                limit=self.max_connections_per_host,
                limit_per_host=self.max_connections_per_host,
                ttl_dns_cache=300,
                use_dns_cache=True,
                ssl=ssl_context if use_ssl else None,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            
            # Timeout otimizado
            timeout = aiohttp.ClientTimeout(
                total=30,
                connect=10,
                sock_read=20
            )
            
            self.sessions[session_key] = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': 'TriplePlay-Sentinel/2.0'}
            )
            
        return self.sessions[session_key]
    
    def _generate_cache_key(self, host: str, command: str, parameters: Dict = None) -> str:
        """Gera chave única para cache"""
        cache_data = f"{host}:{command}:{json.dumps(parameters or {}, sort_keys=True)}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Verifica se entrada do cache ainda é válida"""
        if not cache_entry:
            return False
        return (datetime.now() - cache_entry['timestamp']).total_seconds() < self.cache_ttl
    
    async def execute_api_command(
        self, 
        host: str, 
        username: str, 
        password: str,
        command: str,
        parameters: Dict = None,
        port: int = 8728,
        use_ssl: bool = True,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Executa comando via API MikroTik REST
        
        Args:
            host: IP do MikroTik
            username: Usuário da API
            password: Senha da API
            command: Comando da API (ex: /ip/address/print)
            parameters: Parâmetros do comando
            port: Porta da API (padrão 8728 para HTTPS)
            use_ssl: Usar HTTPS (recomendado)
            use_cache: Usar cache para comandos de leitura
            
        Returns:
            Dict com resultado da execução
        """
        start_time = datetime.now()
        self._stats['total_requests'] += 1
        self._stats['concurrent_requests'] += 1
        
        try:
            # Verifica cache para comandos de leitura
            cache_key = self._generate_cache_key(host, command, parameters)
            if use_cache and 'print' in command.lower():
                cached = self.response_cache.get(cache_key)
                if self._is_cache_valid(cached):
                    self._stats['cache_hits'] += 1
                    self._stats['concurrent_requests'] -= 1
                    return cached['data']
            
            # Prepara URL da API
            protocol = 'https' if use_ssl else 'http'
            base_url = f"{protocol}://{host}:{port}/rest"
            url = f"{base_url}{command}"
            
            # Autenticação básica
            auth = aiohttp.BasicAuth(username, password)
            
            # Obtém sessão otimizada
            session = await self._get_session(host, port, use_ssl)
            
            # Determina método HTTP baseado no comando
            if any(op in command.lower() for op in ['print', 'get', 'monitor']):
                method = 'GET'
                params = parameters
                json_data = None
            else:
                method = 'POST'
                params = None
                json_data = parameters
            
            # Executa requisição
            async with session.request(
                method=method,
                url=url,
                auth=auth,
                params=params,
                json=json_data
            ) as response:
                
                # Processa resposta
                if response.status == 200:
                    if response.content_type == 'application/json':
                        data = await response.json()
                    else:
                        data = await response.text()
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    self._update_stats(execution_time, True)
                    
                    result = {
                        'status': 'success',
                        'data': data,
                        'execution_time_seconds': execution_time,
                        'timestamp': datetime.now().isoformat(),
                        'method': method,
                        'url': url,
                        'cached': False
                    }
                    
                    # Salva no cache se for comando de leitura
                    if use_cache and 'print' in command.lower():
                        self.response_cache[cache_key] = {
                            'data': result,
                            'timestamp': datetime.now()
                        }
                    
                    return result
                    
                else:
                    error_text = await response.text()
                    execution_time = (datetime.now() - start_time).total_seconds()
                    self._update_stats(execution_time, False)
                    
                    return {
                        'status': 'error',
                        'error': f'HTTP {response.status}: {error_text}',
                        'execution_time_seconds': execution_time,
                        'timestamp': datetime.now().isoformat(),
                        'method': method,
                        'url': url
                    }
                    
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(execution_time, False)
            
            return {
                'status': 'error',
                'error': f'Erro na API MikroTik: {str(e)}',
                'execution_time_seconds': execution_time,
                'timestamp': datetime.now().isoformat()
            }
        finally:
            self._stats['concurrent_requests'] -= 1
    
    def execute_command_sync(self, *args, **kwargs) -> Dict[str, Any]:
        """Wrapper síncrono para execute_api_command"""
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.execute_api_command(*args, **kwargs))
    
    async def execute_batch_commands(
        self,
        host: str,
        username: str,
        password: str,
        commands: List[Dict[str, Any]],
        max_concurrent: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Executa múltiplos comandos em paralelo (máxima concorrência)
        
        Args:
            host: IP do MikroTik
            username: Usuário
            password: Senha
            commands: Lista de comandos [{command, parameters}, ...]
            max_concurrent: Máximo de comandos simultâneos
            
        Returns:
            Lista com resultados de todos os comandos
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(cmd_info):
            async with semaphore:
                return await self.execute_api_command(
                    host=host,
                    username=username,
                    password=password,
                    command=cmd_info.get('command'),
                    parameters=cmd_info.get('parameters'),
                    use_cache=cmd_info.get('use_cache', True)
                )
        
        # Executa todos os comandos em paralelo
        tasks = [execute_with_semaphore(cmd) for cmd in commands]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processa resultados e exceções
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'status': 'error',
                    'error': f'Exceção no comando {i}: {str(result)}',
                    'command': commands[i].get('command', 'unknown'),
                    'timestamp': datetime.now().isoformat()
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def execute_multiple_hosts(
        self,
        hosts_config: List[Dict[str, Any]],
        command: str,
        parameters: Dict = None,
        max_concurrent_hosts: int = 20
    ) -> Dict[str, Any]:
        """
        Executa comando em múltiplos MikroTiks simultaneamente
        
        Args:
            hosts_config: Lista de configs [{host, username, password}, ...]
            command: Comando a executar
            parameters: Parâmetros do comando
            max_concurrent_hosts: Máximo de hosts simultâneos
            
        Returns:
            Dict com resultados por host
        """
        def execute_on_host(host_config):
            return {
                'host': host_config['host'],
                'result': self.execute_command_sync(
                    host=host_config['host'],
                    username=host_config['username'],
                    password=host_config['password'],
                    command=command,
                    parameters=parameters
                )
            }
        
        # Usa ThreadPoolExecutor para execução paralela
        results = {}
        with ThreadPoolExecutor(max_workers=max_concurrent_hosts) as executor:
            future_to_host = {
                executor.submit(execute_on_host, config): config['host'] 
                for config in hosts_config
            }
            
            for future in as_completed(future_to_host):
                host = future_to_host[future]
                try:
                    result = future.result()
                    results[host] = result['result']
                except Exception as e:
                    results[host] = {
                        'status': 'error',
                        'error': f'Erro na execução: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    }
        
        return results
    
    def _update_stats(self, execution_time: float, success: bool):
        """Atualiza estatísticas de performance"""
        if success:
            self._stats['successful_requests'] += 1
        else:
            self._stats['failed_requests'] += 1
        
        self._stats['total_response_time'] += execution_time
        self._stats['avg_response_time'] = (
            self._stats['total_response_time'] / self._stats['total_requests']
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de performance"""
        total_requests = self._stats['total_requests']
        return {
            'total_requests': total_requests,
            'successful_requests': self._stats['successful_requests'],
            'failed_requests': self._stats['failed_requests'],
            'success_rate_percent': (
                (self._stats['successful_requests'] / max(1, total_requests)) * 100
            ),
            'cache_hits': self._stats['cache_hits'],
            'cache_hit_rate_percent': (
                (self._stats['cache_hits'] / max(1, total_requests)) * 100
            ),
            'concurrent_requests': self._stats['concurrent_requests'],
            'avg_response_time_seconds': self._stats['avg_response_time'],
            'active_sessions': len(self.sessions),
            'cache_entries': len(self.response_cache)
        }
    
    def clear_cache(self):
        """Limpa cache de respostas"""
        self.response_cache.clear()
        logger.info("Cache de respostas limpo")
    
    async def close_all_sessions(self):
        """Fecha todas as sessões HTTP"""
        for session in self.sessions.values():
            await session.close()
        self.sessions.clear()
        logger.info("Todas as sessões HTTP fechadas")
    
    def test_api_connection(
        self, 
        host: str, 
        username: str, 
        password: str,
        port: int = 8728,
        use_ssl: bool = True
    ) -> Dict[str, Any]:
        """
        Testa conectividade via API MikroTik
        
        Args:
            host: IP do MikroTik
            username: Usuário
            password: Senha
            port: Porta da API
            use_ssl: Usar HTTPS
            
        Returns:
            Dict com resultado do teste
        """
        try:
            # Testa com comando simples
            result = self.execute_command_sync(
                host=host,
                username=username,
                password=password,
                command='/system/identity/print',
                port=port,
                use_ssl=use_ssl,
                use_cache=False
            )
            
            if result['status'] == 'success':
                return {
                    'status': 'success',
                    'message': 'Conexão API MikroTik estabelecida com sucesso',
                    'execution_time_seconds': result['execution_time_seconds'],
                    'system_identity': result.get('data', {}),
                    'protocol': 'HTTPS' if use_ssl else 'HTTP',
                    'port': port,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Erro na API MikroTik: {result.get("error", "Erro desconhecido")}',
                    'execution_time_seconds': result.get('execution_time_seconds', 0),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erro no teste de conexão API: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }


# Instância global do conector API-only
mikrotik_api = MikroTikAPIConnector()
