#!/usr/bin/env python3
"""
TriplePlay-Sentinel Collector Package
Sistema de Monitoramento Centralizado MikroTik-Zabbix via HTTP Agent (PULL)

Este package implementa um collector HTTP inteligente que atua como intermediário
entre o Zabbix e dispositivos MikroTik, executando testes de conectividade sob demanda
através de uma arquitetura PULL otimizada.

Componentes principais:
- config: Configurações centralizadas do sistema
- models: Modelos de dados e estruturas
- cache: Sistema de cache inteligente com TTL
- mikrotik_connector: Conector API nativo para dispositivos MikroTik
- processor: Processador de resultados de testes
- sentinel_api_server: Aplicação Flask principal com API REST

Versão: 2.1.0
"""

__version__ = "2.0.0"
__author__ = "TriplePlay Team"
__email__ = "support@tripleplay.com"

# Imports principais para facilitar uso do package
from .sentinel_config import config_api as config
from .models import TestResult, TestParameters, SystemStats
from .cache import cache
from .mikrotik_connector import MikroTikConnector
from .processor import processor

__all__ = [
    'config',
    'TestResult',
    'TestParameters', 
    'SystemStats',
    'cache',
    'MikroTikConnector',
    'processor'
]