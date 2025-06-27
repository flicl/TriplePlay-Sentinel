#!/usr/bin/env python3
"""
TriplePlay-Sentinel - Modelos de Dados
Sistema de Monitoramento Centralizado MikroTik-Zabbix via HTTP Agent (PULL)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class TestResult:
    """Resultado de um teste de conectividade"""
    status: str
    test_type: str
    timestamp: str
    cache_hit: bool
    cache_ttl: int
    mikrotik_host: str
    target: str
    results: Dict[str, Any]
    raw_output: str = ""
    error_message: str = ""
    execution_time_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização JSON"""
        return {
            'status': self.status,
            'test_type': self.test_type,
            'timestamp': self.timestamp,
            'cache_hit': self.cache_hit,
            'cache_ttl': self.cache_ttl,
            'mikrotik_host': self.mikrotik_host,
            'target': self.target,
            'results': self.results,
            'raw_output': self.raw_output,
            'error_message': self.error_message,
            'execution_time_seconds': self.execution_time_seconds
        }


@dataclass
class CacheEntry:
    """Entrada do cache com timestamp de expiração"""
    result: TestResult
    expiry: datetime
    
    def is_expired(self) -> bool:
        """Verifica se a entrada expirou"""
        return datetime.now() >= self.expiry


@dataclass
class SSHConnectionInfo:
    """Informações de conexão SSH para MikroTik"""
    host: str
    username: str
    password: str
    port: int = 22
    timeout: int = 30
    
    def to_key(self) -> str:
        """Gera chave única para pool de conexões"""
        return f"{self.host}:{self.port}:{self.username}"


@dataclass
class TestParameters:
    """Parâmetros para execução de testes"""
    mikrotik_host: str
    mikrotik_user: str
    mikrotik_password: str
    test_type: str
    target: str
    mikrotik_port: int = 22
    count: int = 4
    size: int = 64
    interval: int = 1
    port: int = 80
    
    def to_cache_key(self) -> str:
        """Gera chave única para cache"""
        import hashlib
        import json
        
        key_data = {
            'host': self.mikrotik_host,
            'mikrotik_port': self.mikrotik_port,
            'type': self.test_type,
            'target': self.target,
            'count': self.count,
            'size': self.size,
            'interval': self.interval,
            'port': self.port
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()


@dataclass
class SystemStats:
    """Estatísticas do sistema"""
    cache_size: int
    active_connections: int
    uptime_seconds: float
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def success_rate(self) -> float:
        """Taxa de sucesso das requisições"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def cache_hit_rate(self) -> float:
        """Taxa de acertos do cache"""
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return (self.cache_hits / total_cache_requests) * 100