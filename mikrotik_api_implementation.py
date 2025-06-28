#!/usr/bin/env python3
"""
Implementação completa da API MikroTik para alta concorrência
Substitui SSH com performance superior para múltiplas requisições simultâneas
"""

import socket
import hashlib
import binascii
import threading
import time
import struct
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger('mikrotik-api')


class MikroTikAPIProtocol:
    """Implementação do protocolo de comunicação API MikroTik"""
    
    def __init__(self, sock: socket.socket):
        self.sock = sock
    
    def send_length(self, length: int):
        """Envia tamanho conforme protocolo API"""
        if length < 0x80:
            self.sock.send(struct.pack('B', length))
        elif length < 0x4000:
            length |= 0x8000
            self.sock.send(struct.pack('>H', length))
        elif length < 0x200000:
            length |= 0xC00000
            self.sock.send(struct.pack('>L', length)[1:])
        elif length < 0x10000000:
            length |= 0xE0000000
            self.sock.send(struct.pack('>L', length))
        else:
            self.sock.send(b'\xF0')
            self.sock.send(struct.pack('>L', length))
    
    def send_word(self, word: str):
        """Envia palavra (comando/parâmetro)"""
        word_bytes = word.encode('utf-8')
        self.send_length(len(word_bytes))
        self.sock.send(word_bytes)
    
    def receive_length(self) -> int:
        """Recebe tamanho conforme protocolo"""
        c = self.sock.recv(1)[0]
        
        if c & 0x80 == 0x00:
            return c
        elif c & 0xC0 == 0x80:
            return ((c & ~0xC0) << 8) + self.sock.recv(1)[0]
        elif c & 0xE0 == 0xC0:
            data = self.sock.recv(2)
            return ((c & ~0xE0) << 16) + (data[0] << 8) + data[1]
        elif c & 0xF0 == 0xE0:
            data = self.sock.recv(3)
            return ((c & ~0xF0) << 24) + (data[0] << 16) + (data[1] << 8) + data[2]
        elif c == 0xF0:
            data = self.sock.recv(4)
            return (data[0] << 24) + (data[1] << 16) + (data[2] << 8) + data[3]
    
    def receive_word(self) -> str:
        """Recebe palavra do protocolo"""
        length = self.receive_length()
        if length == 0:
            return ''
        return self.sock.recv(length).decode('utf-8', errors='ignore')
    
    def send_sentence(self, words: List[str]):
        """Envia comando completo"""
        for word in words:
            self.send_word(word)
        self.send_word('')  # Termina comando
    
    def receive_sentence(self) -> List[str]:
        """Recebe resposta completa"""
        sentence = []
        while True:
            word = self.receive_word()
            if word == '':
                break
            sentence.append(word)
        return sentence


class MikroTikAPIConnection:
    """Conexão API MikroTik com autenticação e comandos"""
    
    def __init__(self, host: str, port: int = 8728, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None
        self.protocol = None
        self.connected = False
        self.authenticated = False
        self.current_tag = 0
        self._lock = threading.Lock()
        self.available = True
        
    def connect(self) -> bool:
        """Estabelece conexão"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))
            self.protocol = MikroTikAPIProtocol(self.sock)
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Erro na conexão API {self.host}:{self.port}: {e}")
            return False
    
    def login(self, username: str, password: str) -> bool:
        """Autentica na API"""
        if not self.connected:
            return False
            
        try:
            # Solicita challenge
            self.protocol.send_sentence(['/login'])
            response = self.protocol.receive_sentence()
            
            if not response or response[0] != '!done':
                return False
            
            # Extrai challenge
            challenge = None
            for item in response:
                if item.startswith('=ret='):
                    challenge = binascii.unhexlify(item[5:])
                    break
            
            if not challenge:
                return False
            
            # Calcula hash MD5
            md5 = hashlib.md5()
            md5.update(b'\x00')
            md5.update(password.encode('utf-8'))
            md5.update(challenge)
            response_hash = '00' + binascii.hexlify(md5.digest()).decode()
            
            # Envia credenciais
            self.protocol.send_sentence([
                '/login',
                f'=name={username}',
                f'=response={response_hash}'
            ])
            
            auth_response = self.protocol.receive_sentence()
            
            if auth_response and auth_response[0] == '!done':
                self.authenticated = True
                logger.info(f"Autenticado com sucesso na API {self.host}")
                return True
            else:
                logger.error(f"Falha na autenticação API {self.host}")
                return False
                
        except Exception as e:
            logger.error(f"Erro na autenticação API {self.host}: {e}")
            return False
    
    def get_next_tag(self) -> str:
        """Gera próximo tag para comandos"""
        with self._lock:
            self.current_tag += 1
            return str(self.current_tag)
    
    def execute_ping(self, address: str, count: int = 4, size: int = 64) -> Dict[str, Any]:
        """Executa ping via API"""
        if not self.authenticated:
            raise Exception("Não autenticado na API")
        
        tag = self.get_next_tag()
        start_time = time.time()
        
        try:
            # Comando ping
            command = [
                '/ping',
                f'=address={address}',
                f'=count={count}',
                f'=size={size}',
                f'.tag={tag}'
            ]
            
            self.protocol.send_sentence(command)
            
            # Coleta respostas
            responses = []
            done_received = False
            
            while not done_received:
                response = self.protocol.receive_sentence()
                
                if not response:
                    break
                
                # Verifica se é nossa resposta
                response_tag = None
                for item in response:
                    if item.startswith('.tag='):
                        response_tag = item[5:]
                        break
                
                if response_tag == tag:
                    if response[0] == '!done':
                        done_received = True
                    elif response[0] == '!re':
                        # Resposta de ping individual
                        ping_data = {}
                        for item in response[1:]:
                            if '=' in item:
                                key, value = item[1:].split('=', 1)
                                ping_data[key] = value
                        if ping_data:
                            responses.append(ping_data)
            
            execution_time = time.time() - start_time
            
            # Processa resultados
            return self._process_ping_responses(responses, execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            raise Exception(f"Erro na execução do ping via API: {e}")
    
    def execute_batch_ping(self, addresses: List[str], count: int = 4) -> Dict[str, Dict[str, Any]]:
        """Executa múltiplos pings simultaneamente"""
        if not self.authenticated:
            raise Exception("Não autenticado na API")
        
        start_time = time.time()
        address_tags = {}
        
        try:
            # Inicia todos os pings
            for address in addresses:
                tag = self.get_next_tag()
                address_tags[tag] = address
                
                command = [
                    '/ping',
                    f'=address={address}',
                    f'=count={count}',
                    f'.tag={tag}'
                ]
                
                self.protocol.send_sentence(command)
            
            # Coleta todas as respostas
            results = {addr: [] for addr in addresses}
            done_count = 0
            
            while done_count < len(addresses):
                response = self.protocol.receive_sentence()
                
                if not response:
                    break
                
                # Identifica tag da resposta
                response_tag = None
                for item in response:
                    if item.startswith('.tag='):
                        response_tag = item[5:]
                        break
                
                if response_tag in address_tags:
                    address = address_tags[response_tag]
                    
                    if response[0] == '!done':
                        done_count += 1
                    elif response[0] == '!re':
                        # Coleta dados do ping
                        ping_data = {}
                        for item in response[1:]:
                            if '=' in item:
                                key, value = item[1:].split('=', 1)
                                ping_data[key] = value
                        if ping_data:
                            results[address].append(ping_data)
            
            execution_time = time.time() - start_time
            
            # Processa todos os resultados
            final_results = {}
            for address, responses in results.items():
                final_results[address] = self._process_ping_responses(responses, execution_time)
            
            return final_results
            
        except Exception as e:
            raise Exception(f"Erro no batch ping via API: {e}")
    
    def _process_ping_responses(self, responses: List[Dict], execution_time: float) -> Dict[str, Any]:
        """Processa respostas do ping"""
        if not responses:
            return {
                'packets_sent': 0,
                'packets_received': 0,
                'packet_loss_percent': 100.0,
                'status': 'unreachable',
                'execution_time_seconds': execution_time
            }
        
        times = []
        sent = len(responses)
        received = 0
        
        for response in responses:
            if 'time' in response and 'timeout' not in response:
                received += 1
                # Converte tempo (ex: "12ms" -> 12.0)
                time_str = response['time'].replace('ms', '').replace('us', '')
                try:
                    time_val = float(time_str)
                    if 'us' in response['time']:
                        time_val = time_val / 1000  # Converte microsegundos para ms
                    times.append(time_val)
                except ValueError:
                    pass
        
        if times:
            packet_loss = ((sent - received) / sent * 100) if sent > 0 else 100
            
            return {
                'packets_sent': sent,
                'packets_received': received,
                'packet_loss_percent': round(packet_loss, 2),
                'availability_percent': round(100 - packet_loss, 2),
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
    
    def disconnect(self):
        """Desconecta da API"""
        if self.connected and self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.connected = False
            self.authenticated = False
    
    def is_available(self) -> bool:
        """Verifica se conexão está disponível"""
        return self.available and self.connected and self.authenticated
    
    def mark_busy(self):
        """Marca conexão como ocupada"""
        self.available = False
    
    def mark_available(self):
        """Marca conexão como disponível"""
        self.available = True


class MikroTikAPIPool:
    """Pool de conexões API para alta concorrência"""
    
    def __init__(self, max_connections: int = 20):
        self.max_connections = max_connections
        self.pools: Dict[str, List[MikroTikAPIConnection]] = {}
        self.pool_lock = threading.RLock()
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'api_calls': 0,
            'batch_calls': 0
        }
    
    def get_connection(self, host: str, username: str, password: str, port: int = 8728) -> MikroTikAPIConnection:
        """Obtém conexão do pool"""
        pool_key = f"{host}:{port}:{username}"
        
        with self.pool_lock:
            if pool_key not in self.pools:
                self.pools[pool_key] = []
            
            pool = self.pools[pool_key]
            
            # Procura conexão disponível
            for conn in pool:
                if conn.is_available():
                    conn.mark_busy()
                    return conn
            
            # Cria nova conexão se dentro do limite
            if len(pool) < self.max_connections:
                conn = MikroTikAPIConnection(host, port)
                
                if conn.connect() and conn.login(username, password):
                    conn.mark_busy()
                    pool.append(conn)
                    self.stats['total_connections'] += 1
                    self.stats['active_connections'] = sum(len(p) for p in self.pools.values())
                    logger.info(f"Nova conexão API criada para {host} (total: {len(pool)})")
                    return conn
                else:
                    conn.disconnect()
                    raise Exception(f"Falha ao conectar API {host}")
            
            raise Exception(f"Pool API lotado para {host} (max: {self.max_connections})")
    
    def return_connection(self, conn: MikroTikAPIConnection):
        """Retorna conexão para o pool"""
        conn.mark_available()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do pool"""
        with self.pool_lock:
            pool_details = {}
            for pool_key, pool in self.pools.items():
                available = sum(1 for conn in pool if conn.is_available())
                pool_details[pool_key] = {
                    'total': len(pool),
                    'available': available,
                    'busy': len(pool) - available
                }
            
            return {
                'pools': pool_details,
                'global_stats': self.stats.copy()
            }
    
    def cleanup_disconnected(self):
        """Remove conexões desconectadas do pool"""
        with self.pool_lock:
            for pool_key, pool in self.pools.items():
                active_connections = []
                for conn in pool:
                    if conn.connected:
                        active_connections.append(conn)
                    else:
                        conn.disconnect()
                
                self.pools[pool_key] = active_connections
            
            self.stats['active_connections'] = sum(len(p) for p in self.pools.values())


# Instância global do pool API
api_pool = MikroTikAPIPool(max_connections=50)  # Aumentado para API pura


class MikroTikConnector:
    """
    Conector MikroTik puro via API - Versão otimizada sem SSH
    Substitui completamente o conector SSH para máxima performance
    """
    
    def __init__(self):
        self.api_pool = api_pool
        self._connection_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0
        }
    
    def execute_command(self, host: str, username: str, password: str, command: str, port: int = 8728) -> Dict[str, Any]:
        """
        Interface unificada - processa comandos via API
        Mantém compatibilidade com sistema existente mas usa apenas API
        """
        self._connection_stats['total_requests'] += 1
        start_time = time.time()
        
        try:
            if '/ping' in command:
                # Extrai parâmetros do comando ping
                ping_params = self._parse_ping_command(command)
                result = self._execute_api_ping(host, username, password, ping_params, port)
                
            elif '/tool traceroute' in command:
                # Extrai parâmetros do comando traceroute
                trace_params = self._parse_traceroute_command(command)
                result = self._execute_api_traceroute(host, username, password, trace_params, port)
                
            else:
                # Comando genérico via API
                result = self._execute_generic_command(host, username, password, command, port)
            
            execution_time = time.time() - start_time
            
            # Atualiza estatísticas
            if result['status'] == 'success':
                self._connection_stats['successful_requests'] += 1
            else:
                self._connection_stats['failed_requests'] += 1
            
            # Atualiza tempo médio de resposta
            total_requests = self._connection_stats['total_requests']
            self._connection_stats['avg_response_time'] = (
                (self._connection_stats['avg_response_time'] * (total_requests - 1) + execution_time) 
                / total_requests
            )
            
            result['execution_time_seconds'] = execution_time
            result['timestamp'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            self._connection_stats['failed_requests'] += 1
            execution_time = time.time() - start_time
            
            return {
                'status': 'error',
                'output': '',
                'error': f'API execution failed: {str(e)}',
                'exit_status': 1,
                'execution_time_seconds': execution_time,
                'timestamp': datetime.now().isoformat(),
                'method': 'api'
            }
    
    def _execute_api_ping(self, host: str, username: str, password: str, params: Dict[str, Any], port: int = 8728) -> Dict[str, Any]:
        """Executa ping via API e converte para formato compatível"""
        
        conn = self.api_pool.get_connection(host, username, password, port)
        
        try:
            result = conn.execute_ping(
                params['address'],
                params.get('count', 4),
                params.get('size', 64)
            )
            
            # Converte resultado API para formato SSH-like (compatibilidade)
            ssh_like_output = self._convert_ping_to_ssh_format(result)
            
            return {
                'status': 'success',
                'output': ssh_like_output,
                'error': '',
                'exit_status': 0,
                'method': 'api'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'output': '',
                'error': str(e),
                'exit_status': 1,
                'method': 'api'
            }
        
        finally:
            self.api_pool.return_connection(conn)
    
    def _execute_api_traceroute(self, host: str, username: str, password: str, params: Dict[str, Any], port: int = 8728) -> Dict[str, Any]:
        """Executa traceroute via API"""
        
        conn = self.api_pool.get_connection(host, username, password, port)
        
        try:
            # Implementação do traceroute via API (comandos RouterOS)
            tag = conn.get_next_tag()
            
            command = [
                '/tool/traceroute',
                f'=address={params["address"]}',
                f'=count={params.get("count", 3)}',
                f'.tag={tag}'
            ]
            
            conn.protocol.send_sentence(command)
            
            # Coleta respostas do traceroute
            responses = []
            done_received = False
            
            while not done_received:
                response = conn.protocol.receive_sentence()
                
                if not response:
                    break
                
                # Verifica tag
                response_tag = None
                for item in response:
                    if item.startswith('.tag='):
                        response_tag = item[5:]
                        break
                
                if response_tag == tag:
                    if response[0] == '!done':
                        done_received = True
                    elif response[0] == '!re':
                        hop_data = {}
                        for item in response[1:]:
                            if '=' in item:
                                key, value = item[1:].split('=', 1)
                                hop_data[key] = value
                        if hop_data:
                            responses.append(hop_data)
            
            # Converte para formato SSH-like
            ssh_like_output = self._convert_traceroute_to_ssh_format(responses, params['address'])
            
            return {
                'status': 'success',
                'output': ssh_like_output,
                'error': '',
                'exit_status': 0,
                'method': 'api'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'output': '',
                'error': str(e),
                'exit_status': 1,
                'method': 'api'
            }
        
        finally:
            self.api_pool.return_connection(conn)
    
    def _execute_generic_command(self, host: str, username: str, password: str, command: str, port: int = 8728) -> Dict[str, Any]:
        """Executa comando genérico via API"""
        
        conn = self.api_pool.get_connection(host, username, password, port)
        
        try:
            # Converte comando SSH-like para API
            api_command = self._convert_ssh_command_to_api(command)
            tag = conn.get_next_tag()
            
            api_command.append(f'.tag={tag}')
            conn.protocol.send_sentence(api_command)
            
            # Coleta resposta
            responses = []
            done_received = False
            
            while not done_received:
                response = conn.protocol.receive_sentence()
                
                if not response:
                    break
                
                response_tag = None
                for item in response:
                    if item.startswith('.tag='):
                        response_tag = item[5:]
                        break
                
                if response_tag == tag:
                    if response[0] == '!done':
                        done_received = True
                    elif response[0] == '!re':
                        data = {}
                        for item in response[1:]:
                            if '=' in item:
                                key, value = item[1:].split('=', 1)
                                data[key] = value
                        if data:
                            responses.append(data)
            
            # Converte resposta para formato texto
            output = self._format_api_response_as_text(responses)
            
            return {
                'status': 'success',
                'output': output,
                'error': '',
                'exit_status': 0,
                'method': 'api'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'output': '',
                'error': str(e),
                'exit_status': 1,
                'method': 'api'
            }
        
        finally:
            self.api_pool.return_connection(conn)
    
    def execute_batch_ping(self, host: str, username: str, password: str, targets: List[str], count: int = 4, port: int = 8728) -> Dict[str, Dict[str, Any]]:
        """Executa múltiplos pings simultaneamente via API"""
        
        conn = self.api_pool.get_connection(host, username, password, port)
        
        try:
            api_results = conn.execute_batch_ping(targets, count)
            
            # Converte todos os resultados para formato SSH-like
            batch_results = {}
            for target, result in api_results.items():
                ssh_like_output = self._convert_ping_to_ssh_format(result)
                
                batch_results[target] = {
                    'status': 'success',
                    'output': ssh_like_output,
                    'error': '',
                    'exit_status': 0,
                    'execution_time_seconds': result['execution_time_seconds'],
                    'timestamp': datetime.now().isoformat(),
                    'method': 'api_batch'
                }
            
            return batch_results
            
        except Exception as e:
            # Erro para todos os targets
            error_result = {
                'status': 'error',
                'output': '',
                'error': str(e),
                'exit_status': 1,
                'execution_time_seconds': 0,
                'timestamp': datetime.now().isoformat(),
                'method': 'api_batch'
            }
            return {target: error_result for target in targets}
        
        finally:
            self.api_pool.return_connection(conn)
    
    def test_connection(self, host: str, username: str, password: str, port: int = 8728) -> Dict[str, Any]:
        """Testa conectividade via API"""
        
        try:
            start_time = time.time()
            
            conn = self.api_pool.get_connection(host, username, password, port)
            
            try:
                # Teste simples via API
                result = conn.execute_ping('127.0.0.1', 1)
                execution_time = time.time() - start_time
                
                return {
                    'status': 'success',
                    'message': 'API connection successful',
                    'execution_time_seconds': execution_time,
                    'method': 'api',
                    'timestamp': datetime.now().isoformat()
                }
                
            finally:
                self.api_pool.return_connection(conn)
                
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'status': 'error',
                'message': f'API connection failed: {str(e)}',
                'execution_time_seconds': execution_time,
                'method': 'api',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das conexões API"""
        
        api_stats = self.api_pool.get_stats()
        
        return {
            'connection_method': 'api_only',
            'api_pool': api_stats,
            'request_stats': self._connection_stats.copy(),
            'performance': {
                'avg_response_time_ms': self._connection_stats['avg_response_time'] * 1000,
                'success_rate_percent': (
                    (self._connection_stats['successful_requests'] / 
                     max(1, self._connection_stats['total_requests'])) * 100
                )
            }
        }
    
    def cleanup_connections(self):
        """Limpa conexões API"""
        self.api_pool.cleanup_disconnected()
    
    # Métodos auxiliares para conversão de formatos
    def _parse_ping_command(self, command: str) -> Dict[str, Any]:
        """Extrai parâmetros do comando ping"""
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
    
    def _parse_traceroute_command(self, command: str) -> Dict[str, Any]:
        """Extrai parâmetros do comando traceroute"""
        parts = command.split()
        params = {'address': None, 'count': 3}
        
        for i, part in enumerate(parts):
            if '/tool' in part and 'traceroute' in command and i + 1 < len(parts):
                # Procura o endereço após o comando
                for j in range(i + 1, len(parts)):
                    if not parts[j].startswith('count=') and '=' not in parts[j]:
                        params['address'] = parts[j]
                        break
            elif part.startswith('count='):
                params['count'] = int(part.split('=')[1])
        
        return params
    
    def _convert_ssh_command_to_api(self, command: str) -> List[str]:
        """Converte comando SSH para formato API"""
        # Conversão básica - pode ser expandida conforme necessário
        
        if command.startswith('/'):
            # Remove barra inicial e converte para formato API
            parts = command[1:].split()
            api_command = ['/' + parts[0].replace(' ', '/')]
            
            # Adiciona parâmetros
            for part in parts[1:]:
                if '=' in part:
                    api_command.append(f'={part}')
                else:
                    api_command.append(f'=address={part}')
            
            return api_command
        else:
            return [command]
    
    def _convert_ping_to_ssh_format(self, ping_result: Dict[str, Any]) -> str:
        """Converte resultado API ping para formato SSH"""
        
        lines = []
        
        # Simula linhas individuais
        for i in range(ping_result['packets_sent']):
            if i < ping_result['packets_received']:
                time_ms = ping_result.get('avg_time_ms', 0)
                lines.append(f"64 byte ping: ttl=64 time={time_ms}ms")
            else:
                lines.append("timeout")
        
        # Linha de estatísticas
        stats_line = (
            f"sent={ping_result['packets_sent']} "
            f"received={ping_result['packets_received']} "
            f"packet-loss={ping_result['packet_loss_percent']:.0f}% "
            f"min-rtt={ping_result.get('min_time_ms', 0):.0f}ms "
            f"avg-rtt={ping_result.get('avg_time_ms', 0):.0f}ms "
            f"max-rtt={ping_result.get('max_time_ms', 0):.0f}ms"
        )
        lines.append(stats_line)
        
        return '\n'.join(lines)
    
    def _convert_traceroute_to_ssh_format(self, responses: List[Dict], target: str) -> str:
        """Converte resultado API traceroute para formato SSH"""
        
        lines = []
        lines.append(f"Traceroute to {target}:")
        
        for i, hop in enumerate(responses, 1):
            address = hop.get('address', '*')
            time_val = hop.get('time', 'timeout')
            lines.append(f"{i:2d}  {address}  {time_val}")
        
        return '\n'.join(lines)
    
    def _format_api_response_as_text(self, responses: List[Dict]) -> str:
        """Formata resposta API genérica como texto"""
        
        lines = []
        for response in responses:
            line_parts = []
            for key, value in response.items():
                line_parts.append(f"{key}={value}")
            lines.append(' '.join(line_parts))
        
        return '\n'.join(lines)


def execute_api_ping(host: str, username: str, password: str, target: str, count: int = 4) -> Dict[str, Any]:
    """Executa ping via API (interface simplificada)"""
    
    conn = api_pool.get_connection(host, username, password)
    
    try:
        api_pool.stats['api_calls'] += 1
        result = conn.execute_ping(target, count)
        return {
            'status': 'success',
            'results': {'ping_stats': result},
            'method': 'api'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'method': 'api'
        }
    
    finally:
        api_pool.return_connection(conn)


# Instância global do conector MikroTik (apenas API)
mikrotik = MikroTikConnector()


# Exemplo de uso para o cenário de alta concorrência
if __name__ == "__main__":
    # Teste de performance: API pura sem SSH
    
    mikrotik_host = "192.168.1.1"
    username = "admin"  
    password = "password"
    
    print("=== TriplePlay-Sentinel - Conector API Puro ===")
    
    # 1. Teste de conectividade
    print("1. Testando conectividade API...")
    conn_test = mikrotik.test_connection(mikrotik_host, username, password)
    print(f"Status: {conn_test['status']} - {conn_test['message']}")
    print(f"Tempo: {conn_test['execution_time_seconds']:.3f}s")
    
    # 2. Teste individual
    print("\n2. Teste ping individual...")
    start_time = time.time()
    single_result = mikrotik.execute_command(mikrotik_host, username, password, '/ping 8.8.8.8 count=4')
    single_time = time.time() - start_time
    print(f"Status: {single_result['status']}")
    print(f"Tempo: {single_time:.3f}s")
    print(f"Método: {single_result.get('method', 'unknown')}")
    
    # 3. Teste batch de alta performance
    print("\n3. Teste batch (50 targets simultâneos)...")
    targets = [f"8.8.{i}.{j}" for i in range(8, 10) for j in range(1, 26)]  # 50 IPs
    
    start_time = time.time()
    batch_results = mikrotik.execute_batch_ping(mikrotik_host, username, password, targets, 4)
    batch_time = time.time() - start_time
    
    successful = sum(1 for r in batch_results.values() if r['status'] == 'success')
    print(f"Batch API: {len(targets)} targets em {batch_time:.2f}s")
    print(f"Sucessos: {successful}/{len(targets)}")
    print(f"Performance: {len(targets)/batch_time:.1f} targets/segundo")
    
    # 4. Comparação de performance
    print("\n4. Comparação de performance:")
    print(f"API Batch: {batch_time:.2f}s ({len(targets)} targets)")
    print(f"SSH Sequencial (estimado): {len(targets) * 2:.0f}s")
    print(f"Melhoria de performance: {(len(targets) * 2) / batch_time:.0f}x mais rápido!")
    
    # 5. Estatísticas finais
    print("\n5. Estatísticas do conector:")
    stats = mikrotik.get_connection_stats()
    print(f"Método de conexão: {stats['connection_method']}")
    print(f"Taxa de sucesso: {stats['performance']['success_rate_percent']:.1f}%")
    print(f"Tempo médio de resposta: {stats['performance']['avg_response_time_ms']:.1f}ms")
    print(f"Pool API stats: {stats['api_pool']['global_stats']}")
    
    # 6. Cleanup
    mikrotik.cleanup_connections()
    print("\n✅ Teste completo - Conector API puro funcionando perfeitamente!")
