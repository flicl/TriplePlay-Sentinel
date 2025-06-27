#!/usr/bin/env python3
"""
TriplePlay-Sentinel - Conector MikroTik
Sistema de Monitoramento Centralizado MikroTik-Zabbix via HTTP Agent (PULL)
"""

import time
import threading
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import paramiko
from config import config
from models import SSHConnectionInfo

logger = logging.getLogger('sentinel-mikrotik')


class MikroTikConnector:
    """
    Conector otimizado para dispositivos MikroTik via SSH com pool de conexões
    """
    
    def __init__(self):
        self.ssh_pool: Dict[str, paramiko.SSHClient] = {}
        self.ssh_lock = threading.RLock()
        self._connection_stats = {
            'total_connections': 0,
            'reused_connections': 0,
            'failed_connections': 0,
            'active_connections': 0
        }
    
    def execute_command(self, host: str, username: str, password: str, command: str, port: int = 22) -> Dict[str, Any]:
        """
        Executa comando no MikroTik via SSH
        
        Args:
            host: Endereço IP do MikroTik
            username: Usuário SSH
            password: Senha SSH
            command: Comando a ser executado
            port: Porta SSH (padrão 22)
            
        Returns:
            Dict com resultado da execução
        """
        start_time = datetime.now()
        
        for attempt in range(config.SSH_MAX_RETRIES):
            try:
                ssh = self._get_ssh_connection(host, username, password, port)
                
                logger.info(f"Executando comando em {host}: {command}")
                stdin, stdout, stderr = ssh.exec_command(command, timeout=config.REQUEST_TIMEOUT)
                
                # Aguarda execução e coleta resultados
                exit_status = stdout.channel.recv_exit_status()
                output = stdout.read().decode('utf-8').strip()
                error = stderr.read().decode('utf-8').strip()
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                if exit_status == 0:
                    logger.info(f"Comando executado com sucesso em {host} ({execution_time:.2f}s)")
                    return {
                        'status': 'success',
                        'output': output,
                        'error': error,
                        'exit_status': exit_status,
                        'execution_time_seconds': execution_time,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"Comando falhou em {host} com exit status {exit_status}")
                    return {
                        'status': 'error',
                        'output': output,
                        'error': error,
                        'exit_status': exit_status,
                        'execution_time_seconds': execution_time,
                        'timestamp': datetime.now().isoformat()
                    }
                    
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1}/{config.SSH_MAX_RETRIES} falhou para {host}: {str(e)}")
                
                # Remove conexão problemática do pool
                self._remove_connection_from_pool(host, username, port)
                
                if attempt == config.SSH_MAX_RETRIES - 1:
                    execution_time = (datetime.now() - start_time).total_seconds()
                    self._connection_stats['failed_connections'] += 1
                    return {
                        'status': 'error',
                        'output': '',
                        'error': f'Erro de conexão após {config.SSH_MAX_RETRIES} tentativas: {str(e)}',
                        'exit_status': -1,
                        'execution_time_seconds': execution_time,
                        'timestamp': datetime.now().isoformat()
                    }
                
                # Aguarda antes da próxima tentativa
                time.sleep(1 * (attempt + 1))
    
    def _get_ssh_connection(self, host: str, username: str, password: str, port: int = 22) -> paramiko.SSHClient:
        """
        Obtém conexão SSH reutilizável do pool
        
        Args:
            host: Endereço IP
            username: Usuário SSH
            password: Senha SSH
            port: Porta SSH (padrão 22)
            
        Returns:
            Cliente SSH conectado
        """
        with self.ssh_lock:
            pool_key = f"{host}:{port}:{username}"
            
            # Verifica se já existe conexão ativa no pool
            if pool_key in self.ssh_pool:
                ssh = self.ssh_pool[pool_key]
                try:
                    # Testa se a conexão ainda está ativa
                    transport = ssh.get_transport()
                    if transport and transport.is_active():
                        logger.debug(f"Reutilizando conexão SSH para {host}")
                        self._connection_stats['reused_connections'] += 1
                        return ssh
                    else:
                        # Conexão morta, remove do pool
                        del self.ssh_pool[pool_key]
                        logger.debug(f"Conexão SSH para {host} estava morta, removida do pool")
                except:
                    # Erro ao testar conexão, remove do pool
                    del self.ssh_pool[pool_key]
                    logger.debug(f"Erro ao testar conexão SSH para {host}, removida do pool")
            
            # Cria nova conexão
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                logger.info(f"Estabelecendo nova conexão SSH para {host}:{port}")
                ssh.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=config.SSH_TIMEOUT,
                    look_for_keys=False,
                    allow_agent=False,
                    banner_timeout=30,
                    auth_timeout=30
                )
                
                # Adiciona ao pool
                self.ssh_pool[pool_key] = ssh
                self._connection_stats['total_connections'] += 1
                self._connection_stats['active_connections'] = len(self.ssh_pool)
                
                logger.info(f"Conexão SSH estabelecida com sucesso para {host}:{port}")
                return ssh
                
            except Exception as e:
                logger.error(f"Erro ao conectar SSH em {host}:{port}: {str(e)}")
                try:
                    ssh.close()
                except:
                    pass
                self._connection_stats['failed_connections'] += 1
                raise
    
    def _remove_connection_from_pool(self, host: str, username: str, port: int = 22):
        """Remove conexão problemática do pool"""
        with self.ssh_lock:
            pool_key = f"{host}:{port}:{username}"
            if pool_key in self.ssh_pool:
                try:
                    self.ssh_pool[pool_key].close()
                except:
                    pass
                del self.ssh_pool[pool_key]
                self._connection_stats['active_connections'] = len(self.ssh_pool)
                logger.debug(f"Conexão SSH removida do pool: {pool_key}")
    
    def cleanup_connections(self):
        """Limpa todas as conexões SSH do pool"""
        with self.ssh_lock:
            for ssh in self.ssh_pool.values():
                try:
                    ssh.close()
                except:
                    pass
            self.ssh_pool.clear()
            self._connection_stats['active_connections'] = 0
            logger.info("Pool de conexões SSH limpo")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das conexões"""
        with self.ssh_lock:
            return {
                'active_connections': len(self.ssh_pool),
                'total_connections': self._connection_stats['total_connections'],
                'reused_connections': self._connection_stats['reused_connections'],
                'failed_connections': self._connection_stats['failed_connections'],
                'reuse_rate_percent': (
                    (self._connection_stats['reused_connections'] / 
                     max(1, self._connection_stats['total_connections'])) * 100
                ) if self._connection_stats['total_connections'] > 0 else 0
            }
    
    def test_connection(self, host: str, username: str, password: str, port: int = 22) -> Dict[str, Any]:
        """
        Testa conectividade SSH com um dispositivo MikroTik
        
        Args:
            host: Endereço IP
            username: Usuário SSH
            password: Senha SSH
            port: Porta SSH (padrão 22)
            
        Returns:
            Dict com resultado do teste
        """
        try:
            start_time = datetime.now()
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=config.SSH_TIMEOUT,
                look_for_keys=False,
                allow_agent=False
            )
            
            # Testa comando simples
            stdin, stdout, stderr = ssh.exec_command('/system identity print', timeout=10)
            output = stdout.read().decode('utf-8').strip()
            
            ssh.close()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'status': 'success',
                'message': 'Conexão SSH estabelecida com sucesso',
                'execution_time_seconds': execution_time,
                'system_identity': output,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                'status': 'error',
                'message': f'Erro na conexão SSH: {str(e)}',
                'execution_time_seconds': execution_time,
                'timestamp': datetime.now().isoformat()
            }


# Instância global do conector
mikrotik = MikroTikConnector()