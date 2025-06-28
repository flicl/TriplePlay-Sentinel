#!/usr/bin/env python3
"""
Proposta de melhoria: Pool de múltiplas conexões SSH por MikroTik
"""

import threading
import time
from typing import Dict, List
import paramiko


class OptimizedMikroTikConnector:
    """
    Conector otimizado com múltiplas conexões SSH por dispositivo
    """
    
    def __init__(self, max_connections_per_host: int = 5):
        self.max_connections_per_host = max_connections_per_host
        self.ssh_pools: Dict[str, List[Dict]] = {}  # host -> lista de conexões
        self.ssh_lock = threading.RLock()
        self._connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'concurrent_commands': 0
        }
    
    def _get_pool_key(self, host: str, port: int, username: str) -> str:
        """Gera chave do pool"""
        return f"{host}:{port}:{username}"
    
    def _get_available_connection(self, host: str, username: str, password: str, port: int = 22):
        """
        Obtém conexão disponível do pool ou cria nova até o limite
        """
        pool_key = self._get_pool_key(host, port, username)
        
        with self.ssh_lock:
            # Inicializa pool se não existir
            if pool_key not in self.ssh_pools:
                self.ssh_pools[pool_key] = []
            
            pool = self.ssh_pools[pool_key]
            
            # Procura conexão disponível
            for conn_info in pool:
                if conn_info['available'] and conn_info['connection'].get_transport().is_active():
                    conn_info['available'] = False
                    conn_info['last_used'] = time.time()
                    return conn_info
            
            # Cria nova conexão se dentro do limite
            if len(pool) < self.max_connections_per_host:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                try:
                    ssh.connect(
                        hostname=host,
                        port=port,
                        username=username,
                        password=password,
                        timeout=30,
                        look_for_keys=False,
                        allow_agent=False
                    )
                    
                    conn_info = {
                        'connection': ssh,
                        'available': False,
                        'created': time.time(),
                        'last_used': time.time()
                    }
                    
                    pool.append(conn_info)
                    self._connection_stats['total_connections'] += 1
                    self._connection_stats['active_connections'] = sum(len(p) for p in self.ssh_pools.values())
                    
                    return conn_info
                    
                except Exception as e:
                    raise Exception(f"Erro ao criar conexão SSH: {str(e)}")
            
            # Pool lotado, aguarda conexão disponível
            return None
    
    def _return_connection(self, pool_key: str, conn_info: Dict):
        """Retorna conexão para o pool"""
        with self.ssh_lock:
            conn_info['available'] = True
            # Pool não precisa ser modificado, apenas marca como disponível
    
    def execute_command_concurrent(self, host: str, username: str, password: str, command: str, port: int = 22):
        """
        Executa comando com suporte a múltiplas conexões simultâneas
        """
        start_time = time.time()
        pool_key = self._get_pool_key(host, port, username)
        
        # Tentativa de obter conexão (com retry)
        conn_info = None
        max_wait = 30  # 30 segundos máximo de espera
        
        while not conn_info and (time.time() - start_time) < max_wait:
            conn_info = self._get_available_connection(host, username, password, port)
            if not conn_info:
                time.sleep(0.1)  # Aguarda 100ms antes de tentar novamente
        
        if not conn_info:
            raise Exception(f"Timeout: Não foi possível obter conexão SSH para {host}")
        
        try:
            ssh = conn_info['connection']
            self._connection_stats['concurrent_commands'] += 1
            
            # Executa comando
            stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
            
            # Aguarda execução
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()
            
            execution_time = time.time() - start_time
            
            return {
                'status': 'success' if exit_status == 0 else 'error',
                'output': output,
                'error': error,
                'exit_status': exit_status,
                'execution_time_seconds': execution_time,
                'connection_pool_key': pool_key,
                'concurrent_commands': self._connection_stats['concurrent_commands']
            }
            
        except Exception as e:
            raise Exception(f"Erro na execução: {str(e)}")
        
        finally:
            # Retorna conexão para o pool
            self._return_connection(pool_key, conn_info)
            self._connection_stats['concurrent_commands'] -= 1
    
    def get_pool_stats(self) -> Dict:
        """Retorna estatísticas dos pools"""
        with self.ssh_lock:
            pool_stats = {}
            for pool_key, pool in self.ssh_pools.items():
                available = sum(1 for conn in pool if conn['available'])
                pool_stats[pool_key] = {
                    'total_connections': len(pool),
                    'available_connections': available,
                    'busy_connections': len(pool) - available
                }
            
            return {
                'pools': pool_stats,
                'global_stats': self._connection_stats,
                'max_connections_per_host': self.max_connections_per_host
            }


# Exemplo de uso:
"""
connector = OptimizedMikroTikConnector(max_connections_per_host=5)

# 5 threads podem executar simultaneamente no mesmo MikroTik
import concurrent.futures

def test_ping(target):
    return connector.execute_command_concurrent(
        '192.168.1.1', 'admin', 'password', 
        f'/ping {target} count=4'
    )

targets = ['8.8.8.8', '1.1.1.1', '8.8.4.4', '208.67.222.222', '9.9.9.9']

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(test_ping, target) for target in targets]
    results = [future.result() for future in futures]

# Resultado: 5 pings executando SIMULTANEAMENTE no mesmo MikroTik
"""
