#!/usr/bin/env python3
"""
config.py - Gerenciador de configuração para o Sentinel Collector

Este módulo implementa o gerenciamento de configuração para o collector,
permitindo o uso de variáveis de ambiente, arquivos de configuração e
criptografia de dados sensíveis.

Autor: TriplePlay Team
Data: Maio 2025
"""

import os
import json
import logging
import base64
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger('sentinel-collector.config')

class ConfigManager:
    """Gerencia configurações do collector com suporte a criptografia"""
    
    def __init__(self, config_path: Optional[str] = None, env_file: Optional[str] = None):
        """
        Inicializa o gerenciador de configuração
        
        Args:
            config_path: Caminho para o arquivo de configuração JSON (opcional)
            env_file: Caminho para o arquivo .env (opcional)
        """
        # Carrega variáveis de ambiente primeiro
        load_dotenv(dotenv_path=env_file)
        
        # Configurações padrão
        self._config = {
            'server': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False,
                'timeout': 5,
                'ssl_cert': '',
                'ssl_key': ''
            },
            'security': {
                'enable_encryption': False,
                'encryption_key': '',
                'salt': '',
            },
            'mikrotik': {
                'default_user': '',
                'default_password': '',
                'connection_timeout': 10,
                'retry_count': 2
            },
            'cache': {
                'enabled': True,
                'ttl': 300  # 5 minutos
            },
            'logging': {
                'level': 'INFO',
                'file': 'collector.log',
                'max_size': 10485760,  # 10MB
                'backup_count': 5
            }
        }
        
        # Sobrescreve com arquivo de configuração se fornecido
        if config_path:
            self._load_config_file(config_path)
            
        # Sobrescreve com variáveis de ambiente
        self._load_from_env()
        
        # Inicializa sistema de criptografia se habilitado
        self._cipher = None
        if self.get('security.enable_encryption'):
            self._setup_encryption()

    def _load_config_file(self, config_path: str) -> None:
        """Carrega configurações de um arquivo JSON"""
        try:
            path = Path(config_path)
            if path.exists() and path.is_file():
                with open(path, 'r') as f:
                    file_config = json.load(f)
                    self._update_nested_dict(self._config, file_config)
                logger.info(f"Configurações carregadas de {config_path}")
            else:
                logger.warning(f"Arquivo de configuração não encontrado: {config_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo de configuração: {str(e)}")
    
    def _load_from_env(self) -> None:
        """Carrega configurações de variáveis de ambiente"""
        # Mapeamento de variáveis de ambiente para chaves de configuração
        env_mapping = {
            'HOST': 'server.host',
            'PORT': 'server.port',
            'DEBUG_MODE': 'server.debug',
            'DEFAULT_TIMEOUT': 'server.timeout',
            'SSL_CERT_PATH': 'server.ssl_cert',
            'SSL_KEY_PATH': 'server.ssl_key',
            'ENABLE_ENCRYPTION': 'security.enable_encryption',
            'ENCRYPTION_KEY': 'security.encryption_key',
            'ENCRYPTION_SALT': 'security.salt',
            'MIKROTIK_USER': 'mikrotik.default_user',
            'MIKROTIK_PASSWORD': 'mikrotik.default_password',
            'MIKROTIK_TIMEOUT': 'mikrotik.connection_timeout',
            'MIKROTIK_RETRY_COUNT': 'mikrotik.retry_count',
            'CACHE_ENABLED': 'cache.enabled',
            'CACHE_TTL': 'cache.ttl',
            'LOG_LEVEL': 'logging.level',
            'LOG_FILE': 'logging.file',
            'LOG_MAX_SIZE': 'logging.max_size',
            'LOG_BACKUP_COUNT': 'logging.backup_count'
        }
        
        # Atualiza configurações com variáveis de ambiente
        for env_var, config_key in env_mapping.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                # Converte para tipo apropriado
                if config_key.endswith(('.port', '.timeout', '.ttl', '.max_size', 
                                     '.backup_count', '.retry_count')):
                    try:
                        value = int(value)
                    except ValueError:
                        logger.warning(f"Valor inválido para {env_var}: {value}. Usando padrão.")
                        continue
                elif config_key.endswith(('.debug', '.enabled', '.enable_encryption')):
                    value = value.lower() in ('true', 'yes', '1', 't', 'y')
                
                # Atualiza configuração
                self.set(config_key, value)
        
        logger.debug("Configurações atualizadas com variáveis de ambiente")
    
    def _update_nested_dict(self, d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza um dicionário aninhado com outro dicionário"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = self._update_nested_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    def _setup_encryption(self) -> None:
        """Configura o sistema de criptografia para dados sensíveis"""
        try:
            key = self.get('security.encryption_key')
            salt = self.get('security.salt')
            
            if not key:
                logger.warning("Chave de criptografia não definida. Usando chave padrão (inseguro!)")
                key = "sentinel_default_key"  # Chave insegura, apenas para desenvolvimento
            
            if not salt:
                salt = os.urandom(16)
                salt_b64 = base64.b64encode(salt).decode('utf-8')
                self.set('security.salt', salt_b64)
                logger.info("Novo salt gerado para criptografia")
            else:
                try:
                    salt = base64.b64decode(salt)
                except Exception:
                    logger.warning("Salt inválido. Gerando novo salt.")
                    salt = os.urandom(16)
                    salt_b64 = base64.b64encode(salt).decode('utf-8')
                    self.set('security.salt', salt_b64)
            
            # Deriva uma chave segura usando PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
            
            # Inicializa o objeto Fernet para criptografia
            self._cipher = Fernet(derived_key)
            logger.info("Sistema de criptografia inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao configurar criptografia: {str(e)}")
            self._cipher = None
    
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
            value = self._config
            for part in parts:
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, path: str, value: Any) -> None:
        """
        Define uma configuração pelo caminho
        
        Args:
            path: Caminho da configuração no formato "secao.chave"
            value: Valor a ser definido
        """
        parts = path.split('.')
        config = self._config
        
        # Navega na estrutura aninhada até o penúltimo nível
        for part in parts[:-1]:
            if part not in config:
                config[part] = {}
            config = config[part]
        
        # Define o valor
        config[parts[-1]] = value
    
    def encrypt(self, data: str) -> str:
        """
        Criptografa uma string
        
        Args:
            data: Dados a serem criptografados
            
        Returns:
            String criptografada em base64
        """
        if not self._cipher:
            logger.warning("Tentativa de criptografia sem sistema inicializado")
            return data
        
        try:
            encrypted = self._cipher.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao criptografar dados: {str(e)}")
            return data
    
    def decrypt(self, data: str) -> str:
        """
        Descriptografa uma string
        
        Args:
            data: Dados criptografados em base64
            
        Returns:
            String descriptografada
        """
        if not self._cipher:
            logger.warning("Tentativa de descriptografia sem sistema inicializado")
            return data
        
        try:
            encrypted = base64.b64decode(data)
            decrypted = self._cipher.decrypt(encrypted)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao descriptografar dados: {str(e)}")
            return data
    
    def save_to_file(self, file_path: str) -> bool:
        """
        Salva as configurações em um arquivo JSON
        
        Args:
            file_path: Caminho para o arquivo
            
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            # Cria diretório se não existir
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Salva configurações
            with open(path, 'w') as f:
                # Remove senha antes de salvar
                config_copy = dict(self._config)
                if 'mikrotik' in config_copy and 'default_password' in config_copy['mikrotik']:
                    config_copy['mikrotik']['default_password'] = '********'
                if 'security' in config_copy and 'encryption_key' in config_copy['security']:
                    config_copy['security']['encryption_key'] = '********'
                
                json.dump(config_copy, f, indent=2)
            
            logger.info(f"Configurações salvas em {file_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {str(e)}")
            return False
    
    def get_log_level(self) -> int:
        """Obtém o nível de log configurado como constante do módulo logging"""
        level_str = self.get('logging.level', 'INFO').upper()
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
        return {
            'host': self.get('server.host'),
            'port': self.get('server.port'),
            'debug': self.get('server.debug'),
            'ssl_context': (self.get('server.ssl_cert'), self.get('server.ssl_key')) 
                          if self.get('server.ssl_cert') and self.get('server.ssl_key') else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Retorna todas as configurações como um dicionário"""
        return dict(self._config)


# Instância global do gerenciador de configuração
config = ConfigManager()
