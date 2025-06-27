#!/usr/bin/env python3
"""
TriplePlay-Sentinel - Configurações
Sistema de Monitoramento Centralizado MikroTik-Zabbix via HTTP Agent (PULL)
"""

import os
from typing import Dict, Any


class Config:
    """Configurações centralizadas do sistema"""
    
    # Configurações da API
    API_HOST = os.getenv('COLLECTOR_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('COLLECTOR_PORT', '5000'))
    ENABLE_HTTPS = os.getenv('ENABLE_HTTPS', 'false').lower() == 'true'
    
    # Configurações de Cache
    CACHE_TTL = int(os.getenv('CACHE_TTL', '30'))  # 30 segundos
    MAX_CACHE_SIZE = int(os.getenv('MAX_CACHE_SIZE', '1000'))
    
    # Configurações SSH/MikroTik
    SSH_TIMEOUT = int(os.getenv('SSH_TIMEOUT', '30'))
    SSH_MAX_RETRIES = int(os.getenv('SSH_MAX_RETRIES', '3'))
    
    # Configurações de Performance
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '10'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '60'))
    
    # Configurações de Segurança
    API_KEY = os.getenv('API_KEY')  # Opcional para autenticação
    ENABLE_AUTH = os.getenv('ENABLE_AUTH', 'false').lower() == 'true'
    
    # Configurações de Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.getenv('LOG_FILE', 'sentinel.log')
    
    # Configurações de Debug
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Retorna configurações como dicionário"""
        return {
            'api_host': cls.API_HOST,
            'api_port': cls.API_PORT,
            'enable_https': cls.ENABLE_HTTPS,
            'cache_ttl': cls.CACHE_TTL,
            'max_cache_size': cls.MAX_CACHE_SIZE,
            'ssh_timeout': cls.SSH_TIMEOUT,
            'ssh_max_retries': cls.SSH_MAX_RETRIES,
            'max_workers': cls.MAX_WORKERS,
            'request_timeout': cls.REQUEST_TIMEOUT,
            'enable_auth': cls.ENABLE_AUTH,
            'log_level': cls.LOG_LEVEL,
            'debug': cls.DEBUG
        }


# Instância global de configuração
config = Config()