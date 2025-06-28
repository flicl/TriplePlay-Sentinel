#!/usr/bin/env python3
"""
TriplePlay-Sentinel - Conector MikroTik API-Only
Sistema 100% baseado na API MikroTik usando librouteros
"""

import time
import threading
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
import librouteros
from librouteros.query import Key
from sentinel_config import config_api as config

logger = logging.getLogger('sentinel-mikrotik-api')


class MikroTikAPIConnection:
    """Conexão individual API MikroTik usando librouteros"""
    
    def __init__(self, host: str, username: str, password: str, port: int = 8728, timeout: int = 10):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.connection = None
        self.connected = False
        self.available = True
        self.created_at = time.time()
        self.last_used = time.time()
        self._lock = threading.Lock()
    
    def connect(self) -> bool:
        """Estabelece conexão com a API MikroTik"""
        try:
            self.connection = librouteros.connect(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                timeout=self.timeout
            )
            self.connected = True
            self.last_used = time.time()
            logger.info(f"Conexão API estabelecida com {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao conectar API {self.host}:{self.port}: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Desconecta da API"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            finally:
                self.connection = None
                self.connected = False
    
    def is_alive(self) -> bool:
        """Verifica se a conexão ainda está ativa"""
        if not self.connected or not self.connection:
            return False
        
        try:
            # Testa com comando simples
            list(self.connection('/system/identity/print'))
            return True
        except:
            self.connected = False
            return False
    
    def execute_ping(self, address: str, count: int = 4, size: int = 64, interval: int = 1) -> Dict[str, Any]:
        """Executa ping via API librouteros"""
        if not self.connected or not self.connection:
            raise Exception("Conexão não estabelecida")
        
        start_time = time.time()
        self.last_used = start_time
        
        try:
            # Executa ping usando librouteros
            ping_results = []
            
            # Comando ping via API
            ping_cmd = self.connection('/ping')
            
            # Configura parâmetros
            ping_responses = ping_cmd(
                address=address,
                count=count,
                size=size,
                interval=interval
            )
            
            # Coleta respostas
            for response in ping_responses:
                ping_results.append(response)
            
            execution_time = time.time() - start_time
            
            # Processa resultados
            return self._process_ping_results(ping_results, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Erro no ping via API {self.host}: {e}")
            raise Exception(f"Erro na execução do ping: {e}")
    
    def execute_batch_ping(self, addresses: List[str], count: int = 4, size: int = 64) -> Dict[str, Dict[str, Any]]:
        """Executa múltiplos pings simultaneamente"""
        if not self.connected or not self.connection:
            raise Exception("Conexão não estabelecida")
        
        start_time = time.time()
        self.last_used = start_time
        results = {}
        
        try:
            # Para cada endereço, executa ping
            for address in addresses:
                try:
                    result = self.execute_ping(address, count, size)
                    results[address] = {
                        'status': 'success',
                        'data': result
                    }
                except Exception as e:
                    results[address] = {
                        'status': 'error',
                        'error': str(e),
                        'data': {
                            'packets_sent': 0,
                            'packets_received': 0,
                            'packet_loss_percent': 100.0,
                            'status': 'unreachable'
                        }
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"Erro no batch ping via API {self.host}: {e}")
            # Retorna erro para todos os endereços
            error_data = {
                'packets_sent': 0,
                'packets_received': 0,
                'packet_loss_percent': 100.0,
                'status': 'unreachable'
            }
            return {
                addr: {'status': 'error', 'error': str(e), 'data': error_data} 
                for addr in addresses
            }
    
    def execute_traceroute(self, address: str, max_hops: int = 30) -> Dict[str, Any]:
        """Executa traceroute via API"""
        if not self.connected or not self.connection:
            raise Exception("Conexão não estabelecida")
        
        start_time = time.time()
        self.last_used = start_time
        
        try:
            # Comando traceroute via API
            traceroute_cmd = self.connection('/tool/traceroute')
            
            traceroute_results = []
            traceroute_responses = traceroute_cmd(
                address=address,
                count=max_hops
            )
            
            # Coleta respostas
            for response in traceroute_responses:
                traceroute_results.append(response)
            
            execution_time = time.time() - start_time
            
            # Processa resultados do traceroute
            return self._process_traceroute_results(traceroute_results, address, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Erro no traceroute via API {self.host}: {e}")
            raise Exception(f"Erro na execução do traceroute: {e}")
    
    def _process_ping_results(self, ping_results: List[Dict], execution_time: float) -> Dict[str, Any]:
        """Processa resultados do ping da API librouteros"""
        
        if not ping_results:
            return {
                'packets_sent': 0,
                'packets_received': 0,
                'packet_loss_percent': 100.0,
                'availability_percent': 0.0,
                'status': 'unreachable',
                'execution_time_seconds': execution_time
            }
        
        times = []
        sent = 0
        received = 0
        
        for result in ping_results:
            sent += 1
            
            # Verifica se o ping foi bem-sucedido
            if 'time' in result and 'timeout' not in result:
                received += 1
                
                # Extrai tempo (librouteros já retorna em formato adequado)
                time_str = result['time']
                if isinstance(time_str, str):
                    # Remove sufixos como 'ms', 'us'
                    time_val = time_str.replace('ms', '').replace('us', '').replace('s', '')
                    try:
                        time_float = float(time_val)
                        # Converte para ms se necessário
                        if 'us' in time_str:
                            time_float = time_float / 1000
                        elif 's' in time_str and 'ms' not in time_str:
                            time_float = time_float * 1000
                        times.append(time_float)
                    except ValueError:
                        pass
                elif isinstance(time_str, (int, float)):
                    times.append(float(time_str))
        
        # Calcula estatísticas
        if times:
            packet_loss = ((sent - received) / sent * 100) if sent > 0 else 100
            availability = 100 - packet_loss
            
            return {
                'packets_sent': sent,
                'packets_received': received,
                'packet_loss_percent': round(packet_loss, 2),
                'availability_percent': round(availability, 2),
                'min_time_ms': round(min(times), 2),
                'avg_time_ms': round(sum(times) / len(times), 2),
                'max_time_ms': round(max(times), 2),
                'jitter_ms': round(max(times) - min(times), 2) if len(times) > 1 else 0,
                'status': 'reachable',
                'execution_time_seconds': round(execution_time, 2)
            }
        else:
            return {
                'packets_sent': sent,
                'packets_received': 0,
                'packet_loss_percent': 100.0,
                'availability_percent': 0.0,
                'status': 'unreachable',
                'execution_time_seconds': round(execution_time, 2)
            }
    
    def _process_traceroute_results(self, traceroute_results: List[Dict], target: str, execution_time: float) -> Dict[str, Any]:
        """Processa resultados do traceroute"""
        
        hops = []
        hop_dict = {}
        
        for result in traceroute_results:
            if 'hop' in result:
                hop_num = int(result['hop'])
                hop_info = {
                    'hop': hop_num,
                    'address': result.get('address', '*'),
                    'loss_percent': float(result.get('loss', 100)),
                    'last_time_ms': None,
                    'avg_time_ms': None,
                    'best_time_ms': None,
                    'worst_time_ms': None
                }
                
                # Processa tempos se disponíveis
                for time_key in ['time', 'last', 'avg', 'best', 'worst']:
                    if time_key in result:
                        time_str = str(result[time_key])
                        time_val = self._parse_time_value(time_str)
                        if time_val is not None:
                            if time_key in ['time', 'last']:
                                hop_info['last_time_ms'] = time_val
                            elif time_key == 'avg':
                                hop_info['avg_time_ms'] = time_val
                            elif time_key == 'best':
                                hop_info['best_time_ms'] = time_val
                            elif time_key == 'worst':
                                hop_info['worst_time_ms'] = time_val
                
                hop_dict[hop_num] = hop_info
        
        # Converte para lista ordenada
        hops = [hop_dict[hop_num] for hop_num in sorted(hop_dict.keys())]
        
        # Determina se chegou ao destino
        final_hop = hops[-1] if hops else None
        reached_target = False
        
        if final_hop:
            reached_target = (
                target == final_hop.get('address') or
                final_hop.get('loss_percent', 100) < 100
            )
        
        return {
            'target': target,
            'hop_count': len(hops),
            'hops': hops,
            'reached_target': reached_target,
            'max_hops': len(hops),
            'status': 'success' if reached_target else 'incomplete',
            'execution_time_seconds': round(execution_time, 2)
        }
    
    def _parse_time_value(self, time_str: str) -> Optional[float]:
        """Parse valor de tempo para ms"""
        if not time_str or time_str == '*':
            return None
        
        try:
            # Remove sufixos e converte
            time_val = time_str.replace('ms', '').replace('us', '').replace('s', '')
            time_float = float(time_val)
            
            # Converte para ms
            if 'us' in time_str:
                return time_float / 1000
            elif 's' in time_str and 'ms' not in time_str:
                return time_float * 1000
            else:
                return time_float
                
        except ValueError:
            return None
    
    def mark_busy(self):
        """Marca conexão como ocupada"""
        with self._lock:
            self.available = False
    
    def mark_available(self):
        """Marca conexão como disponível"""
        with self._lock:
            self.available = True
            self.last_used = time.time()
    
    def is_available(self) -> bool:
        """Verifica se conexão está disponível"""
        with self._lock:
            return self.available and self.connected


class MikroTikAPIPool:
    """Pool de conexões API MikroTik usando librouteros"""
    
    def __init__(self, max_connections_per_host: int = 10):
        self.max_connections_per_host = max_connections_per_host
        self.pools: Dict[str, List[MikroTikAPIConnection]] = {}
        self.pool_lock = threading.RLock()
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'api_calls': 0,
            'batch_calls': 0,
            'reused_connections': 0,
            'failed_connections': 0
        }
    
    def _get_pool_key(self, host: str, username: str, port: int) -> str:
        """Gera chave do pool"""
        return f"{host}:{port}:{username}"
    
    @contextmanager
    def get_connection(self, host: str, username: str, password: str, port: int = 8728):
        """Context manager para obter conexão do pool"""
        pool_key = self._get_pool_key(host, username, port)
        connection = None
        
        try:
            # Obtém conexão do pool
            connection = self._acquire_connection(host, username, password, port)
            self.stats['api_calls'] += 1
            yield connection
            
        except Exception as e:
            self.stats['failed_connections'] += 1
            raise e
            
        finally:
            # Retorna conexão para o pool
            if connection:
                self._release_connection(connection)
    
    def _acquire_connection(self, host: str, username: str, password: str, port: int) -> MikroTikAPIConnection:
        """Obtém conexão do pool"""
        pool_key = self._get_pool_key(host, username, port)
        
        with self.pool_lock:
            if pool_key not in self.pools:
                self.pools[pool_key] = []
            
            pool = self.pools[pool_key]
            
            # Procura conexão disponível e ativa
            for conn in pool:
                if conn.is_available() and conn.is_alive():
                    conn.mark_busy()
                    self.stats['reused_connections'] += 1
                    logger.debug(f"Reutilizando conexão API para {host}")
                    return conn
            
            # Remove conexões mortas
            active_connections = []
            for conn in pool:
                if conn.is_alive():
                    active_connections.append(conn)
                else:
                    conn.disconnect()
            self.pools[pool_key] = active_connections
            
            # Cria nova conexão se dentro do limite
            if len(self.pools[pool_key]) < self.max_connections_per_host:
                conn = MikroTikAPIConnection(host, username, password, port)
                
                if conn.connect():
                    conn.mark_busy()
                    self.pools[pool_key].append(conn)
                    self.stats['total_connections'] += 1
                    self.stats['active_connections'] = sum(len(p) for p in self.pools.values())
                    logger.info(f"Nova conexão API criada para {host} (total no pool: {len(self.pools[pool_key])})")
                    return conn
                else:
                    raise Exception(f"Falha ao conectar API {host}:{port}")
            
            raise Exception(f"Pool API lotado para {host} (max: {self.max_connections_per_host})")
    
    def _release_connection(self, connection: MikroTikAPIConnection):
        """Retorna conexão para o pool"""
        connection.mark_available()
    
    def execute_ping(self, host: str, username: str, password: str, address: str, 
                    count: int = 4, size: int = 64, port: int = 8728) -> Dict[str, Any]:
        """Interface simplificada para ping"""
        
        with self.get_connection(host, username, password, port) as conn:
            return conn.execute_ping(address, count, size)
    
    def execute_batch_ping(self, host: str, username: str, password: str, addresses: List[str],
                          count: int = 4, size: int = 64, port: int = 8728) -> Dict[str, Dict[str, Any]]:
        """Interface simplificada para batch ping"""
        
        with self.get_connection(host, username, password, port) as conn:
            self.stats['batch_calls'] += 1
            return conn.execute_batch_ping(addresses, count, size)
    
    def execute_traceroute(self, host: str, username: str, password: str, address: str,
                          max_hops: int = 30, port: int = 8728) -> Dict[str, Any]:
        """Interface simplificada para traceroute"""
        
        with self.get_connection(host, username, password, port) as conn:
            return conn.execute_traceroute(address, max_hops)
    
    def test_connection(self, host: str, username: str, password: str, port: int = 8728) -> Dict[str, Any]:
        """Testa conectividade API"""
        
        start_time = time.time()
        
        try:
            with self.get_connection(host, username, password, port) as conn:
                # Executa comando simples para testar
                test_result = conn.execute_ping('8.8.8.8', 1)
                
                execution_time = time.time() - start_time
                
                return {
                    'status': 'success',
                    'message': 'API connection successful',
                    'response_time_ms': round(execution_time * 1000, 2),
                    'method': 'api',
                    'host': host,
                    'port': port,
                    'test_result': test_result
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'status': 'error',
                'message': f'API connection failed: {str(e)}',
                'response_time_ms': round(execution_time * 1000, 2),
                'method': 'api',
                'host': host,
                'port': port,
                'error': str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do pool"""
        
        with self.pool_lock:
            pool_details = {}
            total_connections = 0
            available_connections = 0
            
            for pool_key, pool in self.pools.items():
                available = sum(1 for conn in pool if conn.is_available())
                busy = len(pool) - available
                
                pool_details[pool_key] = {
                    'total': len(pool),
                    'available': available,
                    'busy': busy
                }
                
                total_connections += len(pool)
                available_connections += available
            
            success_rate = 0
            if self.stats['api_calls'] > 0:
                success_rate = ((self.stats['api_calls'] - self.stats['failed_connections']) / 
                               self.stats['api_calls'] * 100)
            
            reuse_rate = 0
            if self.stats['total_connections'] > 0:
                reuse_rate = (self.stats['reused_connections'] / 
                             self.stats['total_connections'] * 100)
            
            return {
                'pools': pool_details,
                'global_stats': {
                    'total_connections': total_connections,
                    'available_connections': available_connections,
                    'busy_connections': total_connections - available_connections,
                    'api_calls': self.stats['api_calls'],
                    'batch_calls': self.stats['batch_calls'],
                    'failed_connections': self.stats['failed_connections'],
                    'success_rate_percent': round(success_rate, 2),
                    'reuse_rate_percent': round(reuse_rate, 2)
                },
                'performance': {
                    'max_connections_per_host': self.max_connections_per_host,
                    'library': 'librouteros',
                    'connection_type': 'api_native'
                }
            }
    
    def cleanup_idle_connections(self, max_idle_time: int = 300):
        """Remove conexões ociosas"""
        
        current_time = time.time()
        
        with self.pool_lock:
            for pool_key, pool in self.pools.items():
                active_connections = []
                
                for conn in pool:
                    if conn.is_available() and (current_time - conn.last_used) > max_idle_time:
                        logger.debug(f"Removendo conexão ociosa: {pool_key}")
                        conn.disconnect()
                    else:
                        active_connections.append(conn)
                
                self.pools[pool_key] = active_connections
            
            self.stats['active_connections'] = sum(len(p) for p in self.pools.values())
    
    def cleanup_all_connections(self):
        """Limpa todas as conexões"""
        
        with self.pool_lock:
            for pool in self.pools.values():
                for conn in pool:
                    conn.disconnect()
            
            self.pools.clear()
            self.stats['active_connections'] = 0
            logger.info("Todas as conexões API foram limpas")


# Instância global do pool
mikrotik_api_pool = MikroTikAPIPool(max_connections_per_host=config.MAX_API_CONNECTIONS)


# Interface compatível com o sistema existente
class MikroTikConnector:
    """Interface compatível para substituir o conector SSH"""
    
    def __init__(self):
        self.api_pool = mikrotik_api_pool
    
    def execute_command(self, host: str, username: str, password: str, command: str, port: int = 8728) -> Dict[str, Any]:
        """
        Interface compatível que simula comandos SSH via API
        Mantém compatibilidade com o sistema existente
        """
        
        start_time = time.time()
        
        try:
            # Parse do comando para detectar tipo
            if '/ping' in command:
                # Extrai parâmetros do ping
                ping_params = self._parse_ping_command(command)
                
                # Executa via API
                api_result = self.api_pool.execute_ping(
                    host, username, password,
                    ping_params['address'],
                    ping_params.get('count', 4),
                    ping_params.get('size', 64),
                    port
                )
                
                # Converte resultado para formato SSH compatível
                ssh_output = self._convert_ping_to_ssh_format(api_result)
                
                return {
                    'status': 'success',
                    'output': ssh_output,
                    'error': '',
                    'exit_status': 0,
                    'execution_time_seconds': api_result.get('execution_time_seconds', 0),
                    'timestamp': datetime.now().isoformat(),
                    'method': 'api'
                }
                
            elif '/tool/traceroute' in command or 'traceroute' in command:
                # Extrai parâmetros do traceroute
                trace_params = self._parse_traceroute_command(command)
                
                # Executa via API
                api_result = self.api_pool.execute_traceroute(
                    host, username, password,
                    trace_params['address'],
                    trace_params.get('max_hops', 30),
                    port
                )
                
                # Converte resultado para formato SSH compatível
                ssh_output = self._convert_traceroute_to_ssh_format(api_result)
                
                return {
                    'status': 'success',
                    'output': ssh_output,
                    'error': '',
                    'exit_status': 0,
                    'execution_time_seconds': api_result.get('execution_time_seconds', 0),
                    'timestamp': datetime.now().isoformat(),
                    'method': 'api'
                }
            
            else:
                # Comando não suportado
                return {
                    'status': 'error',
                    'output': '',
                    'error': f'Comando não suportado na versão API-only: {command}',
                    'exit_status': 1,
                    'execution_time_seconds': time.time() - start_time,
                    'timestamp': datetime.now().isoformat(),
                    'method': 'api'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'output': '',
                'error': str(e),
                'exit_status': 1,
                'execution_time_seconds': time.time() - start_time,
                'timestamp': datetime.now().isoformat(),
                'method': 'api'
            }
    
    def _parse_ping_command(self, command: str) -> Dict[str, Any]:
        """Extrai parâmetros do comando ping"""
        parts = command.split()
        params = {'address': None, 'count': 4, 'size': 64}
        
        for i, part in enumerate(parts):
            if part == '/ping' and i + 1 < len(parts):
                params['address'] = parts[i + 1]
            elif 'count=' in part:
                params['count'] = int(part.split('=')[1])
            elif 'size=' in part:
                params['size'] = int(part.split('=')[1])
        
        return params
    
    def _parse_traceroute_command(self, command: str) -> Dict[str, Any]:
        """Extrai parâmetros do comando traceroute"""
        parts = command.split()
        params = {'address': None, 'max_hops': 30}
        
        for i, part in enumerate(parts):
            if 'traceroute' in part and i + 1 < len(parts):
                params['address'] = parts[i + 1]
            elif 'count=' in part:
                params['max_hops'] = int(part.split('=')[1])
        
        return params
    
    def _convert_ping_to_ssh_format(self, api_result: Dict[str, Any]) -> str:
        """Converte resultado da API ping para formato SSH"""
        
        lines = []
        
        # Simula linhas individuais de ping
        packets_sent = api_result.get('packets_sent', 0)
        packets_received = api_result.get('packets_received', 0)
        avg_time = api_result.get('avg_time_ms', 0)
        
        for i in range(packets_sent):
            if i < packets_received:
                lines.append(f"64 byte ping: ttl=64 time={avg_time}ms")
            else:
                lines.append("timeout")
        
        # Linha de estatísticas
        stats_line = (
            f"sent={packets_sent} "
            f"received={packets_received} "
            f"packet-loss={api_result.get('packet_loss_percent', 100):.0f}% "
            f"min-rtt={api_result.get('min_time_ms', 0):.0f}ms "
            f"avg-rtt={api_result.get('avg_time_ms', 0):.0f}ms "
            f"max-rtt={api_result.get('max_time_ms', 0):.0f}ms"
        )
        lines.append(stats_line)
        
        return '\n'.join(lines)
    
    def _convert_traceroute_to_ssh_format(self, api_result: Dict[str, Any]) -> str:
        """Converte resultado da API traceroute para formato SSH"""
        
        lines = []
        hops = api_result.get('hops', [])
        
        for hop in hops:
            hop_num = hop.get('hop', 0)
            address = hop.get('address', '*')
            last_time = hop.get('last_time_ms')
            
            if last_time is not None:
                lines.append(f"{hop_num:2d} {address:15s} {last_time:.1f}ms")
            else:
                lines.append(f"{hop_num:2d} {address:15s} *")
        
        return '\n'.join(lines)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das conexões"""
        return self.api_pool.get_stats()
    
    def test_connection(self, host: str, username: str, password: str, port: int = 8728) -> Dict[str, Any]:
        """Testa conectividade"""
        return self.api_pool.test_connection(host, username, password, port)


# Instância global compatível
mikrotik = MikroTikConnector()


if __name__ == "__main__":
    # Teste básico
    print("=== Teste MikroTik API com librouteros ===")
    
    # Configuração de teste
    host = "192.168.1.1"
    username = "admin"
    password = "password"
    
    # Teste de conectividade
    print("1. Testando conectividade...")
    conn_test = mikrotik.test_connection(host, username, password)
    print(f"Status: {conn_test['status']}")
    print(f"Tempo: {conn_test['response_time_ms']}ms")
    
    # Teste de ping individual
    print("\n2. Teste de ping individual...")
    ping_result = mikrotik.execute_command(host, username, password, '/ping 8.8.8.8 count=4')
    print(f"Status: {ping_result['status']}")
    print(f"Método: {ping_result['method']}")
    print(f"Tempo: {ping_result['execution_time_seconds']:.2f}s")
    
    # Teste batch
    print("\n3. Teste batch ping...")
    targets = ['8.8.8.8', '1.1.1.1', '8.8.4.4']
    batch_results = mikrotik_api_pool.execute_batch_ping(host, username, password, targets)
    
    successful = sum(1 for r in batch_results.values() if r['status'] == 'success')
    print(f"Batch: {successful}/{len(targets)} sucessos")
    
    # Estatísticas
    print("\n4. Estatísticas:")
    stats = mikrotik.get_connection_stats()
    print(f"Conexões ativas: {stats['global_stats']['total_connections']}")
    print(f"Taxa de sucesso: {stats['global_stats']['success_rate_percent']}%")
    print(f"Taxa de reuso: {stats['global_stats']['reuse_rate_percent']}%")
    print(f"Biblioteca: {stats['performance']['library']}")
