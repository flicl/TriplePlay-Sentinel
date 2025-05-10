#!/usr/bin/env python3
"""
config_helper.py - Módulo auxiliar para integração do ConfigManager com o collector

Este módulo fornece funções auxiliares para facilitar o uso do ConfigManager
no collector.py.

Autor: TriplePlay Team
Data: Maio 2025
"""

import os
import sys
import logging
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Configuração básica de logging
logger = logging.getLogger('sentinel-collector.config_helper')

# Carrega variáveis de ambiente
load_dotenv()

# Tenta importar o ConfigManager
try:
    from config import ConfigManager
    config_manager_available = True
except ImportError:
    logger.warning("Módulo ConfigManager não encontrado. Usando configurações básicas.")
    config_manager_available = False


class SimpleConfig:
    """Classe simples para gerenciar configurações a partir de variáveis de ambiente"""
    
    def __init__(self):
        """Inicializa a configuração simples"""
        # Configurações do servidor
        self.server = {
            'host': os.getenv('HOST', '0.0.0.0'),
            'port': int(os.getenv('PORT', '5000')),
            'debug': os.getenv('DEBUG_MODE', 'False').lower() in ('true', 'yes', '1', 't', 'y'),
            'timeout': int(os.getenv('DEFAULT_TIMEOUT', '5')),
            'ssl_cert': os.getenv('SSL_CERT_PATH', ''),
            'ssl_key': os.getenv('SSL_KEY_PATH', '')
        }
        
        # Configurações do MikroTik
        self.mikrotik = {
            'default_user': os.getenv('MIKROTIK_USER', ''),
            'default_password': os.getenv('MIKROTIK_PASSWORD', ''),
            'connection_timeout': int(os.getenv('MIKROTIK_TIMEOUT', '10')),
            'retry_count': int(os.getenv('MIKROTIK_RETRY_COUNT', '2'))
        }
        
        # Configurações de log
        self.logging = {
            'level': os.getenv('LOG_LEVEL', 'INFO').upper(),
            'file': os.getenv('LOG_FILE', 'collector.log')
        }
        
        # Configurações de cache
        self.cache = {
            'enabled': os.getenv('CACHE_ENABLED', 'True').lower() in ('true', 'yes', '1', 't', 'y'),
            'ttl': int(os.getenv('CACHE_TTL', '300'))
        }
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Obtém uma configuração pelo caminho
        
        Args:
            path: Caminho da configuração no formato "secao.chave"
            default: Valor padrão se a configuração não existir
            
        Returns:
            Valor da configuração ou valor padrão
        """
        try:
            parts = path.split('.')
            section = parts[0]
            key = parts[1]
            
            if section == 'server':
                return self.server.get(key, default)
            elif section == 'mikrotik':
                return self.mikrotik.get(key, default)
            elif section == 'logging':
                return self.logging.get(key, default)
            elif section == 'cache':
                return self.cache.get(key, default)
            else:
                return default
        except (IndexError, KeyError):
            return default
    
    def get_log_level(self) -> int:
        """Obtém o nível de log configurado como constante do módulo logging"""
        level_str = self.logging.get('level', 'INFO')
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(level_str, logging.INFO)
    
    def get_server_settings(self) -> Dict[str, Any]:
        """Retorna as configurações do servidor web"""
        ssl_context = None
        if self.server['ssl_cert'] and self.server['ssl_key']:
            ssl_context = (self.server['ssl_cert'], self.server['ssl_key'])
            
        return {
            'host': self.server['host'],
            'port': self.server['port'],
            'debug': self.server['debug'],
            'ssl_context': ssl_context
        }


# Inicializa a configuração
if config_manager_available:
    try:
        # Tenta usar o ConfigManager avançado
        from config import config as advanced_config
        config = advanced_config
        logger.info("Usando ConfigManager para gerenciamento de configurações")
    except (ImportError, AttributeError):
        # Fallback para configuração simples
        config = SimpleConfig()
        logger.info("Usando configuração simples (fallback)")
else:
    # Usa a configuração simples
    config = SimpleConfig()
    logger.info("Usando configuração simples")
