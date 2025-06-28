#!/usr/bin/env python3
"""
TriplePlay-Sentinel - Configurações API-Only
Sistema de Monitoramento 100% baseado na API MikroTik (sem SSH)
"""

import os
from typing import Dict, Any


class ConfigAPIOnly:
    """Configurações centralizadas do sistema API-only"""
    
    # Configurações da API
    API_HOST = os.getenv('COLLECTOR_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('COLLECTOR_PORT', '5000'))
    ENABLE_HTTPS = os.getenv('ENABLE_HTTPS', 'false').lower() == 'true'
    
    # Configurações de Cache
    CACHE_TTL = int(os.getenv('CACHE_TTL', '30'))  # 30 segundos
    MAX_CACHE_SIZE = int(os.getenv('MAX_CACHE_SIZE', '1000'))
    
    # Configurações MikroTik API
    MIKROTIK_API_PORT = int(os.getenv('MIKROTIK_API_PORT', '8728'))  # HTTPS API
    MIKROTIK_API_PORT_HTTP = int(os.getenv('MIKROTIK_API_PORT_HTTP', '8729'))  # HTTP API
    MIKROTIK_USE_SSL = os.getenv('MIKROTIK_USE_SSL', 'true').lower() == 'true'
    MIKROTIK_API_TIMEOUT = int(os.getenv('MIKROTIK_API_TIMEOUT', '30'))
    MIKROTIK_MAX_RETRIES = int(os.getenv('MIKROTIK_MAX_RETRIES', '3'))
    
    # Configurações de Concorrência
    MAX_CONCURRENT_HOSTS = int(os.getenv('MAX_CONCURRENT_HOSTS', '50'))
    MAX_CONCURRENT_COMMANDS = int(os.getenv('MAX_CONCURRENT_COMMANDS', '20'))
    MAX_CONNECTIONS_PER_HOST = int(os.getenv('MAX_CONNECTIONS_PER_HOST', '10'))
    
    # Configurações de Performance
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '20'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '60'))
    
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
            'mikrotik_api_port': cls.MIKROTIK_API_PORT,
            'mikrotik_api_port_http': cls.MIKROTIK_API_PORT_HTTP,
            'mikrotik_use_ssl': cls.MIKROTIK_USE_SSL,
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


# Instância global de configuração API-only
config_api = ConfigAPIOnly()
