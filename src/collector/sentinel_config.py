#!/usr/bin/env python3
"""
TriplePlay-Sentinel - System Configuration
Network Monitoring and Management System
"""

import os
from typing import Dict, Any


class SentinelConfig:
    """Configurações centralizadas do sistema"""
    
    # Configurações da API
    API_HOST = os.getenv('COLLECTOR_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('COLLECTOR_PORT', '5000'))
    ENABLE_HTTPS = os.getenv('ENABLE_HTTPS', 'false').lower() == 'true'
    
    # Configurações de Cache - Otimizado para muitas requisições por host
    CACHE_TTL = int(os.getenv('CACHE_TTL', '15'))  # Cache menor para resultados mais frescos
    MAX_CACHE_SIZE = int(os.getenv('MAX_CACHE_SIZE', '5000'))  # Cache maior para mais resultados
    
    # Configurações MikroTik (valores padrão - porta especificada por request)
    MIKROTIK_API_TIMEOUT = int(os.getenv('MIKROTIK_API_TIMEOUT', '30'))
    MIKROTIK_MAX_RETRIES = int(os.getenv('MIKROTIK_MAX_RETRIES', '3'))
    
    # Configurações de Concorrência - Otimizado para poucos MikroTiks com muitas requisições cada
    MAX_CONCURRENT_HOSTS = int(os.getenv('MAX_CONCURRENT_HOSTS', '15'))  # Máximo 15 MikroTiks simultâneos
    MAX_CONCURRENT_COMMANDS = int(os.getenv('MAX_CONCURRENT_COMMANDS', '200'))  # 200 comandos por MikroTik
    MAX_CONNECTIONS_PER_HOST = int(os.getenv('MAX_CONNECTIONS_PER_HOST', '50'))  # 50 conexões por MikroTik
    
    # Configurações de Performance - Ajustado para alta carga por MikroTik
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '50'))  # Mais workers para processar requisições
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '120'))  # Timeout maior para traceroute
    
    # Configurações de Segurança
    API_KEY = os.getenv('API_KEY')  # Opcional para autenticação
    ENABLE_AUTH = os.getenv('ENABLE_AUTH', 'false').lower() == 'true'
    
    # Configurações de Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.getenv('LOG_FILE', 'sentinel-api.log')
    
    # Configurações de Debug
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Configurações de Cache Inteligente
    ENABLE_SMART_CACHE = os.getenv('ENABLE_SMART_CACHE', 'true').lower() == 'true'
    CACHE_COMMANDS = [
        '/system/identity/print',
        '/interface/print',
        '/ip/address/print',
        '/ip/route/print',
        '/system/resource/print'
    ]
    
    # Configurações de Monitoramento
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    METRICS_RETENTION_HOURS = int(os.getenv('METRICS_RETENTION_HOURS', '24'))
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Retorna configurações como dicionário"""
        return {
            'api_host': cls.API_HOST,
            'api_port': cls.API_PORT,
            'enable_https': cls.ENABLE_HTTPS,
            'cache_ttl': cls.CACHE_TTL,
            'max_cache_size': cls.MAX_CACHE_SIZE,
            'mikrotik_api_timeout': cls.MIKROTIK_API_TIMEOUT,
            'mikrotik_max_retries': cls.MIKROTIK_MAX_RETRIES,
            'max_concurrent_hosts': cls.MAX_CONCURRENT_HOSTS,
            'max_concurrent_commands': cls.MAX_CONCURRENT_COMMANDS,
            'max_connections_per_host': cls.MAX_CONNECTIONS_PER_HOST,
            'max_workers': cls.MAX_WORKERS,
            'request_timeout': cls.REQUEST_TIMEOUT,
            'enable_auth': cls.ENABLE_AUTH,
            'log_level': cls.LOG_LEVEL,
            'debug': cls.DEBUG,
            'enable_smart_cache': cls.ENABLE_SMART_CACHE,
            'enable_metrics': cls.ENABLE_METRICS,
            'metrics_retention_hours': cls.METRICS_RETENTION_HOURS
        }


# Instância global de configuração
config = SentinelConfig()
