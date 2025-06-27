# 🌐 RouterOS API Integration

## Visão Geral

O TriplePlay-Sentinel utiliza a **RouterOS API** para comunicação com dispositivos MikroTik, executando comandos de teste de conectividade de forma centralizada. Esta integração elimina a necessidade de scripts locais nos dispositivos.

## 🔗 Conexão RouterOS

### Métodos de Conexão Suportados

#### 1. RouterOS API (Recomendado)
```python
# Configuração da conexão API
connection_config = {
    "host": "192.168.1.1",
    "username": "admin",
    "password": "secure_password",
    "port": 8728,  # API port
    "use_ssl": False,  # Para porta 8729
    "timeout": 10,
    "encoding": "utf-8"
}
```

#### 2. SSH API (Alternativo)
```python
# Configuração SSH quando API não está disponível
ssh_config = {
    "host": "192.168.1.1", 
    "username": "admin",
    "password": "secure_password",
    "port": 22,
    "timeout": 10,
    "key_filename": "/path/to/ssh/key"  # Opcional
}
```

## 🧪 Comandos de Teste Suportados

### 1. Ping Test
Executa teste ICMP através do comando `/ping`.

#### Comando RouterOS
```
/ping address=8.8.8.8 count=4 size=64 interval=1s
```

#### Parâmetros Suportados
| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `address` | string | obrigatório | IP ou hostname de destino |
| `count` | int | 4 | Número de pacotes |
| `size` | int | 64 | Tamanho do pacote (bytes) |
| `interval` | string | "1s" | Intervalo entre pacotes |
| `ttl` | int | 64 | Time to Live |
| `tos` | int | 0 | Type of Service |
| `src-address` | string | auto | IP de origem |
| `routing-table` | string | main | Tabela de roteamento |

#### Output Parsing
```python
# Exemplo de parsing do output do ping
def parse_ping_output(raw_output):
    """
    Parse do output do comando /ping do RouterOS
    
    Input:
      SEQ HOST                                     SIZE TTL TIME  STATUS
        0 8.8.8.8                                    64  56 13ms
        1 8.8.8.8                                    64  56 14ms
        2 8.8.8.8                                    64  56 15ms
        3 8.8.8.8                                    64  56 12ms
        sent=4 received=4 packet-loss=0% min-rtt=12ms avg-rtt=13ms max-rtt=15ms
    """
    
    result = {
        "packets_sent": 0,
        "packets_received": 0,
        "packet_loss_percent": 0,
        "min_time_ms": 0.0,
        "max_time_ms": 0.0,
        "avg_time_ms": 0.0,
        "times": []
    }
    
    # Parsing logic here...
    return result
```

### 2. TCP Connect Test
Testa conectividade TCP usando `/tool tcp-connect`.

#### Comando RouterOS
```
/tool tcp-connect address=www.google.com port=443 timeout=5s
```

#### Parâmetros Suportados
| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `address` | string | obrigatório | IP ou hostname |
| `port` | int | obrigatório | Porta TCP |
| `timeout` | string | "5s" | Timeout da conexão |
| `src-address` | string | auto | IP de origem |
| `routing-table` | string | main | Tabela de roteamento |

#### Output Parsing
```python
def parse_tcp_connect_output(raw_output):
    """
    Parse do output do comando /tool tcp-connect
    
    Input:
    status: connected
    connect-time: 45ms
    local-address: 192.168.1.100:54321
    remote-address: 142.250.185.4:443
    """
    
    result = {
        "connection_successful": False,
        "connect_time_ms": 0.0,
        "local_address": "",
        "remote_address": "",
        "timeout_occurred": False
    }
    
    # Parsing logic here...
    return result
```

### 3. Traceroute Test
Executa traceroute usando `/tool traceroute`.

#### Comando RouterOS
```
/tool traceroute address=8.8.8.8 max-hops=15 timeout=3s
```

#### Parâmetros Suportados
| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `address` | string | obrigatório | IP ou hostname de destino |
| `max-hops` | int | 15 | Máximo de hops |
| `timeout` | string | "3s" | Timeout por hop |
| `src-address` | string | auto | IP de origem |
| `routing-table` | string | main | Tabela de roteamento |

## 🔧 Client Implementation

### RouterOS API Client
```python
import librouteros
from typing import Dict, List, Optional
import logging

class RouterOSClient:
    """Cliente RouterOS API otimizado para testes de conectividade"""
    
    def __init__(self, host: str, username: str, password: str, 
                 port: int = 8728, use_ssl: bool = False, timeout: int = 10):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.connection = None
        
    def connect(self) -> bool:
        """Estabelece conexão com o dispositivo MikroTik"""
        try:
            if self.use_ssl:
                self.connection = librouteros.connect(
                    host=self.host,
                    username=self.username,
                    password=self.password,
                    port=self.port,
                    ssl_wrapper=librouteros.create_ssl_wrapper(),
                    timeout=self.timeout
                )
            else:
                self.connection = librouteros.connect(
                    host=self.host,
                    username=self.username, 
                    password=self.password,
                    port=self.port,
                    timeout=self.timeout
                )
            return True
            
        except Exception as e:
            logging.error(f"Falha na conexão RouterOS {self.host}: {e}")
            return False
    
    def execute_ping(self, target: str, count: int = 4, 
                    size: int = 64, interval: str = "1s") -> Dict:
        """Executa teste de ping"""
        
        command = [
            "/ping",
            f"address={target}",
            f"count={count}",
            f"size={size}",
            f"interval={interval}"
        ]
        
        try:
            result = self.connection(cmd=command)
            return self._parse_ping_result(result)
            
        except Exception as e:
            logging.error(f"Erro no ping {target}: {e}")
            raise
    
    def execute_tcp_connect(self, target: str, port: int, 
                           timeout: str = "5s") -> Dict:
        """Executa teste TCP connect"""
        
        command = [
            "/tool/tcp-connect",
            f"address={target}",
            f"port={port}",
            f"timeout={timeout}"
        ]
        
        try:
            result = self.connection(cmd=command)
            return self._parse_tcp_connect_result(result)
            
        except Exception as e:
            logging.error(f"Erro no TCP connect {target}:{port}: {e}")
            raise
    
    def disconnect(self):
        """Fecha conexão"""
        if self.connection:
            self.connection.close()
            self.connection = None
```

## 🔐 Configuração de Segurança

### Preparação do MikroTik

#### 1. Criar Usuário para Monitoramento
```routeros
# Criar grupo com permissões mínimas
/user group add name=monitoring policy=read,test

# Criar usuário específico para monitoramento
/user add name=sentinel-monitor group=monitoring password=secure_password

# Opcional: Restringir por IP
/user set sentinel-monitor allowed-address=192.168.1.100/32
```

#### 2. Configurar API
```routeros
# Habilitar API na porta padrão
/ip service enable api

# Opcional: Configurar API SSL
/ip service set api-ssl certificate=your-certificate port=8729
/ip service enable api-ssl

# Configurar firewall para API
/ip firewall filter add chain=input action=accept src-address=192.168.1.100/32 dst-port=8728 protocol=tcp comment="Sentinel API Access"
```

#### 3. Configurar SSH (Alternativo)
```routeros
# Habilitar SSH
/ip service enable ssh

# Configurar chaves SSH (recomendado)
/user ssh-keys import public-key-file=sentinel-monitor.pub user=sentinel-monitor

# Desabilitar senha para SSH (opcional)
/user set sentinel-monitor password=""
```

## ⚡ Otimizações de Performance

### Connection Pooling
```python
from typing import Dict
import threading
import time

class RouterOSConnectionPool:
    """Pool de conexões RouterOS para otimizar performance"""
    
    def __init__(self, max_connections: int = 10, 
                 connection_timeout: int = 300):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.pools: Dict[str, List] = {}
        self.lock = threading.Lock()
    
    def get_connection(self, host: str, username: str, 
                      password: str) -> RouterOSClient:
        """Obtém conexão do pool ou cria nova"""
        
        pool_key = f"{host}:{username}"
        
        with self.lock:
            if pool_key not in self.pools:
                self.pools[pool_key] = []
            
            pool = self.pools[pool_key]
            
            # Procura conexão disponível
            for conn_info in pool:
                if conn_info['available'] and not conn_info['expired']:
                    conn_info['available'] = False
                    conn_info['last_used'] = time.time()
                    return conn_info['connection']
            
            # Cria nova conexão se pool não está cheio
            if len(pool) < self.max_connections:
                client = RouterOSClient(host, username, password)
                if client.connect():
                    pool.append({
                        'connection': client,
                        'available': False,
                        'created': time.time(),
                        'last_used': time.time(),
                        'expired': False
                    })
                    return client
            
            raise Exception(f"Pool de conexões lotado para {host}")
    
    def return_connection(self, connection: RouterOSClient):
        """Retorna conexão para o pool"""
        # Implementation here...
        pass
```

### Command Caching
```python
import hashlib
import json
from typing import Dict, Optional

class RouterOSCommandCache:
    """Cache inteligente para comandos RouterOS"""
    
    def __init__(self, ttl_seconds: int = 30):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict] = {}
    
    def _generate_key(self, host: str, command: str, params: Dict) -> str:
        """Gera chave única para o cache"""
        data = {
            'host': host,
            'command': command,
            'params': sorted(params.items())
        }
        return hashlib.md5(json.dumps(data).encode()).hexdigest()
    
    def get(self, host: str, command: str, params: Dict) -> Optional[Dict]:
        """Obtém resultado do cache se válido"""
        key = self._generate_key(host, command, params)
        
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl_seconds:
                return entry['result']
            else:
                del self.cache[key]
        
        return None
    
    def set(self, host: str, command: str, params: Dict, result: Dict):
        """Armazena resultado no cache"""
        key = self._generate_key(host, command, params)
        self.cache[key] = {
            'result': result,
            'timestamp': time.time()
        }
```

## 🔄 Error Handling

### Common RouterOS Errors
```python
class RouterOSError(Exception):
    """Base class for RouterOS errors"""
    pass

class RouterOSConnectionError(RouterOSError):
    """Erro de conexão"""
    pass

class RouterOSAuthenticationError(RouterOSError):
    """Erro de autenticação"""
    pass

class RouterOSCommandError(RouterOSError):
    """Erro de execução de comando"""
    pass

class RouterOSTimeoutError(RouterOSError):
    """Timeout de operação"""
    pass

# Error mapping
ROUTEROS_ERROR_MAP = {
    "cannot connect": RouterOSConnectionError,
    "invalid user name or password": RouterOSAuthenticationError,
    "timeout": RouterOSTimeoutError,
    "command failed": RouterOSCommandError
}
```

### Retry Logic
```python
import time
import random
from functools import wraps

def routeros_retry(max_attempts: int = 3, backoff_factor: float = 1.0):
    """Decorator para retry com backoff exponencial"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except (RouterOSConnectionError, RouterOSTimeoutError) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
                        time.sleep(delay)
                        logging.warning(f"Tentativa {attempt + 1} falhou, tentando novamente em {delay:.2f}s")
                    else:
                        logging.error(f"Todas as {max_attempts} tentativas falharam")
                        
                except RouterOSAuthenticationError:
                    # Não tenta novamente para erros de autenticação
                    raise
            
            raise last_exception
        
        return wrapper
    return decorator
```

## 📊 Monitoring e Logs

### Health Check do Cliente
```python
def health_check(self) -> Dict:
    """Verifica saúde da conexão RouterOS"""
    
    try:
        # Tenta comando simples
        result = self.connection(cmd=["/system/identity/print"])
        
        return {
            "status": "healthy",
            "device_identity": result[0].get('name', 'unknown'),
            "routeros_version": result[0].get('version', 'unknown'),
            "connection_time_ms": self._measure_connection_time(),
            "last_error": None
        }
        
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "connection_time_ms": -1,
            "last_error": str(e)
        }
```

### Logging Format
```python
import logging

# Configuração de log específica para RouterOS
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    level=logging.INFO
)

logger = logging.getLogger('routeros_client')

# Log context
def log_command(host: str, command: str, duration_ms: float, success: bool):
    """Log de execução de comando"""
    
    if success:
        logger.info(f"RouterOS {host}: {command} completed in {duration_ms:.2f}ms")
    else:
        logger.error(f"RouterOS {host}: {command} failed after {duration_ms:.2f}ms")
```

---

**📝 Nota**: Esta integração RouterOS é otimizada para uso em sistemas de monitoramento críticos com foco em performance e confiabilidade.
