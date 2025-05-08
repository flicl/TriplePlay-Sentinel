# Guia de Desenvolvimento do Sentinel

Este guia descreve como configurar o ambiente de desenvolvimento e contribuir para o projeto Sentinel.

## Visão Geral do Código

O Sentinel é composto por vários componentes principais:

1. **collector.py**: API web em Python que recebe requisições do Zabbix e se comunica com dispositivos MikroTik
2. **Dockerfile/docker-compose.yml**: Arquivos para containerização do collector
3. **Template Zabbix**: XML de template para configuração no Zabbix

## Ambiente de Desenvolvimento

### Pré-requisitos

- Python 3.9+
- Docker e Docker Compose
- Git
- Editor de código (recomendado: VS Code, PyCharm)
- Zabbix (para testes) - pode ser usado em container
- Dispositivo MikroTik para testes (pode ser RouterOS em VM)

### Configuração Inicial

1. Clone o repositório:
   ```bash
   git clone https://github.com/tripleplay/sentinel.git
   cd sentinel
   ```

2. Crie e ative um ambiente virtual Python:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # ou
   venv\Scripts\activate.bat  # Windows
   ```

3. Instale as dependências de desenvolvimento:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Configure o arquivo de ambiente para desenvolvimento:
   ```bash
   cp .env.example .env.dev
   # Edite .env.dev com suas configurações
   ```

## Estrutura do Projeto

```
sentinel/
├── app/
│   ├── __init__.py
│   ├── main.py          # Ponto de entrada da aplicação FastAPI
│   ├── config.py        # Configurações e variáveis de ambiente
│   ├── auth.py          # Funções de autenticação
│   ├── routes/
│   │   ├── __init__.py
│   │   └── tests.py     # Endpoints da API
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py   # Modelos Pydantic
│   └── services/
│       ├── __init__.py
│       ├── mikrotik.py  # Lógica de conexão com MikroTik
│       └── tests.py     # Implementação dos testes
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_routes.py
│   └── test_mikrotik.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── README.md
└── zabbix/
    └── templates/
        └── sentinel_template.xml
```

## Desenvolvimento da API

### Servidor Web

O collector usa FastAPI como framework web. O arquivo principal `app/main.py` configura a aplicação:

```python
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.config import Settings
from app.routes import tests

settings = Settings()
app = FastAPI(title="Sentinel Collector API")

# Setup authentication
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

# Register routes
app.include_router(tests.router)
```

### Modelos de Dados

Os schemas Pydantic em `app/models/schemas.py` definem a estrutura dos dados:

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

class TestBase(BaseModel):
    mikrotik_ip: str
    mikrotik_user: str
    mikrotik_pass: str
    mikrotik_port: int = 8728
    target_ip: str
    test_type: Literal["ping", "tcp"]

class PingTest(TestBase):
    test_type: Literal["ping"] = "ping"
    ping_count: int = 5
    ping_timeout: int = 1

class TCPTest(TestBase):
    test_type: Literal["tcp"] = "tcp"
    tcp_port: int

class PingResult(BaseModel):
    status: str
    average_latency_ms: Optional[float] = None
    min_latency_ms: Optional[float] = None
    max_latency_ms: Optional[float] = None
    packet_loss_percent: float
    jitter_ms: Optional[float] = None
    sent: int
    received: int
    error: Optional[str] = None

class TCPResult(BaseModel):
    status: str
    connection_time_ms: Optional[float] = None
    error: Optional[str] = None
```

### Rotas da API

As rotas são definidas em `app/routes/tests.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Security, status
from app.models.schemas import PingTest, TCPTest, PingResult, TCPResult
from app.services.tests import run_ping_test, run_tcp_test
from app.auth import validate_api_key

router = APIRouter(prefix="/run_test", dependencies=[Depends(validate_api_key)])

@router.post("", response_model=PingResult | TCPResult)
async def run_test(test_data: PingTest | TCPTest):
    try:
        if test_data.test_type == "ping":
            return await run_ping_test(test_data)
        elif test_data.test_type == "tcp":
            return await run_tcp_test(test_data)
        else:
            raise HTTPException(status_code=400, detail="Invalid test type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Serviços MikroTik

A lógica de conexão com o MikroTik está em `app/services/mikrotik.py`:

```python
import asyncio
from librouteros import connect
from librouteros.exceptions import ConnectionError, LoginError
import paramiko
import logging
from app.config import Settings
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)
settings = Settings()

@asynccontextmanager
async def mikrotik_connection(host, username, password, port=8728):
    """
    Context manager for MikroTik API connection.
    """
    connection = None
    try:
        # Attempt API connection
        logger.debug(f"Connecting to MikroTik {host}:{port} via API")
        connection = connect(host=host, username=username, password=password, port=port)
        logger.debug(f"Connected to MikroTik {host} via API")
        yield connection, "api"
    except (ConnectionError, LoginError) as e:
        logger.warning(f"API connection failed: {str(e)}, trying SSH")
        try:
            # Fallback to SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=host, username=username, password=password, port=22, timeout=10)
            logger.debug(f"Connected to MikroTik {host} via SSH")
            yield ssh, "ssh"
        except Exception as ssh_error:
            logger.error(f"SSH connection failed: {str(ssh_error)}")
            raise ConnectionError(f"Failed to connect to MikroTik at {host}: {str(e)}. SSH fallback failed: {str(ssh_error)}")
    finally:
        if connection:
            connection.close()
            logger.debug(f"Closed connection to MikroTik {host}")
```

### Implementação dos Testes

A lógica dos testes está em `app/services/tests.py`:

```python
import asyncio
import re
import time
import logging
from app.models.schemas import PingTest, TCPTest, PingResult, TCPResult
from app.services.mikrotik import mikrotik_connection

logger = logging.getLogger(__name__)

async def run_ping_test(test_data: PingTest) -> PingResult:
    """
    Run a ping test on a MikroTik device.
    """
    logger.info(f"Running ping test from {test_data.mikrotik_ip} to {test_data.target_ip}")
    
    try:
        async with mikrotik_connection(
            test_data.mikrotik_ip, test_data.mikrotik_user, test_data.mikrotik_pass, test_data.mikrotik_port
        ) as (connection, conn_type):
            
            if conn_type == "api":
                # Execute via API
                params = {
                    "address": test_data.target_ip,
                    "count": str(test_data.ping_count),
                    "timeout": str(test_data.ping_timeout)
                }
                logger.debug(f"Executing ping via API with params: {params}")
                result = connection('/ping', **params)
                return parse_ping_api_result(result)
            else:
                # Execute via SSH
                command = f"/ping {test_data.target_ip} count={test_data.ping_count} timeout={test_data.ping_timeout}"
                logger.debug(f"Executing command via SSH: {command}")
                stdin, stdout, stderr = connection.exec_command(command)
                result = stdout.read().decode('utf-8')
                return parse_ping_ssh_result(result)
    
    except Exception as e:
        logger.error(f"Error in ping test: {str(e)}")
        return PingResult(
            status="failed",
            packet_loss_percent=100.0,
            sent=test_data.ping_count,
            received=0,
            error=str(e)
        )

async def run_tcp_test(test_data: TCPTest) -> TCPResult:
    """
    Run a TCP connection test on a MikroTik device.
    """
    logger.info(f"Running TCP test from {test_data.mikrotik_ip} to {test_data.target_ip}:{test_data.tcp_port}")
    
    try:
        async with mikrotik_connection(
            test_data.mikrotik_ip, test_data.mikrotik_user, test_data.mikrotik_pass, test_data.mikrotik_port
        ) as (connection, conn_type):
            
            start_time = time.time()
            
            if conn_type == "api":
                # Execute via API
                params = {
                    "url": f"tcp://{test_data.target_ip}:{test_data.tcp_port}",
                    "check-certificate": "no"
                }
                logger.debug(f"Executing TCP test via API with params: {params}")
                try:
                    connection('/tool/fetch', **params)
                    end_time = time.time()
                    return TCPResult(
                        status="success",
                        connection_time_ms=round((end_time - start_time) * 1000, 2)
                    )
                except Exception as e:
                    return TCPResult(
                        status="failed",
                        error=str(e)
                    )
            else:
                # Execute via SSH
                command = f"/tool fetch url=tcp://{test_data.target_ip}:{test_data.tcp_port} check-certificate=no"
                logger.debug(f"Executing command via SSH: {command}")
                stdin, stdout, stderr = connection.exec_command(command)
                result = stdout.read().decode('utf-8')
                error = stderr.read().decode('utf-8')
                
                end_time = time.time()
                
                if error and "failure" in error.lower():
                    return TCPResult(
                        status="failed",
                        error=error.strip()
                    )
                else:
                    return TCPResult(
                        status="success",
                        connection_time_ms=round((end_time - start_time) * 1000, 2)
                    )
    
    except Exception as e:
        logger.error(f"Error in TCP test: {str(e)}")
        return TCPResult(
            status="failed",
            error=str(e)
        )

def parse_ping_api_result(api_result):
    """Parse results from MikroTik API ping command."""
    # Implementation depends on the exact format returned by the MikroTik API
    # This is a simplified example
    total_sent = 0
    total_received = 0
    latencies = []
    
    for packet in api_result:
        total_sent += 1
        if 'time' in packet:
            total_received += 1
            latencies.append(float(packet['time']))
    
    if not latencies:
        return PingResult(
            status="failed" if total_sent > 0 else "error",
            packet_loss_percent=100.0 if total_sent > 0 else 0.0,
            sent=total_sent,
            received=total_received,
            error="No responses received" if total_sent > 0 else "No packets sent"
        )
    
    packet_loss = 100.0 - (total_received / total_sent * 100) if total_sent > 0 else 0.0
    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    
    # Calculate jitter (standard deviation of latencies)
    if len(latencies) >= 2:
        mean_latency = sum(latencies) / len(latencies)
        variance = sum((x - mean_latency) ** 2 for x in latencies) / len(latencies)
        jitter = variance ** 0.5
    else:
        jitter = 0.0
    
    return PingResult(
        status="success",
        average_latency_ms=round(avg_latency, 2),
        min_latency_ms=round(min_latency, 2),
        max_latency_ms=round(max_latency, 2),
        packet_loss_percent=round(packet_loss, 2),
        jitter_ms=round(jitter, 2),
        sent=total_sent,
        received=total_received
    )

def parse_ping_ssh_result(ssh_result):
    """Parse results from MikroTik SSH ping command."""
    # Implementation depends on the exact output format of the MikroTik ping command
    # This is an example that needs to be adjusted based on actual output
    
    sent_match = re.search(r'(\d+) packets transmitted', ssh_result)
    received_match = re.search(r'(\d+) packets received', ssh_result)
    loss_match = re.search(r'(\d+)% packet loss', ssh_result)
    rtt_match = re.search(r'min/avg/max = ([\d.]+)/([\d.]+)/([\d.]+)', ssh_result)
    
    if not sent_match or not received_match:
        return PingResult(
            status="error",
            packet_loss_percent=100.0,
            sent=0,
            received=0,
            error="Could not parse ping results"
        )
    
    sent = int(sent_match.group(1))
    received = int(received_match.group(1))
    loss = float(loss_match.group(1)) if loss_match else 100.0 - (received / sent * 100)
    
    if rtt_match and received > 0:
        min_latency = float(rtt_match.group(1))
        avg_latency = float(rtt_match.group(2))
        max_latency = float(rtt_match.group(3))
        
        # Estimate jitter (this is a simplification)
        jitter = (max_latency - min_latency) / 3
        
        return PingResult(
            status="success",
            average_latency_ms=round(avg_latency, 2),
            min_latency_ms=round(min_latency, 2),
            max_latency_ms=round(max_latency, 2),
            packet_loss_percent=round(loss, 2),
            jitter_ms=round(jitter, 2),
            sent=sent,
            received=received
        )
    else:
        return PingResult(
            status="failed",
            packet_loss_percent=100.0,
            sent=sent,
            received=0,
            error="No response received"
        )
```

## Testes Automatizados

### Configuração de Testes

O projeto usa pytest para testes. Os testes estão no diretório `tests/`.

Exemplo de teste para autenticação (`tests/test_auth.py`):

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app, api_key_header
from app.config import Settings

client = TestClient(app)
settings = Settings()

def test_missing_api_key():
    response = client.get("/healthcheck", headers={})
    assert response.status_code == 200  # Healthcheck doesn't require auth
    
    response = client.post("/run_test", json={})
    assert response.status_code == 403
    
def test_invalid_api_key():
    response = client.post(
        "/run_test", 
        headers={"Authorization": "Bearer invalid_token"},
        json={}
    )
    assert response.status_code == 403

def test_valid_api_key():
    response = client.post(
        "/run_test", 
        headers={"Authorization": f"Bearer {settings.auth_token}"},
        json={}
    )
    # Should fail with 422 (Validation Error) not 403 (Forbidden)
    assert response.status_code == 422
```

### Executando os Testes

```bash
# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=app

# Executar testes específicos
pytest tests/test_auth.py
```

## Construção e Implantação

### Construção Local

```bash
# Construir a imagem Docker
docker build -t sentinel-collector .

# Executar o container
docker run -p 8000:8000 --env-file .env sentinel-collector
```

### Implantação com Docker Compose

```bash
# Desenvolvimento
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Produção
docker-compose up -d
```

## Diretrizes de Contribuição

### Fluxo de Trabalho Git

1. Crie uma branch para sua feature ou correção:
   ```bash
   git checkout -b feature/nome-da-feature
   # ou
   git checkout -b fix/nome-do-bug
   ```

2. Faça suas alterações, seguindo as convenções de código.

3. Escreva/atualize testes automatizados.

4. Execute os testes localmente:
   ```bash
   pytest
   ```

5. Envie suas alterações:
   ```bash
   git commit -m "Descrição clara das alterações"
   git push origin feature/nome-da-feature
   ```

6. Crie um Pull Request no GitHub.

### Convenções de Código

- Siga PEP 8 para formatação do código Python.
- Use docstrings estilo Google para documentação de código.
- Mantenha o código modular e testável.
- Execute o linter antes de enviar código: `flake8 app/ tests/`

### Lançamento de Versões

O projeto segue Versionamento Semântico:

- **MAJOR.MINOR.PATCH** (ex: 1.2.3)
  - **MAJOR**: Mudanças incompatíveis com versões anteriores
  - **MINOR**: Adições de funcionalidades compatíveis
  - **PATCH**: Correções de bugs compatíveis

Para criar uma nova versão:

1. Atualize a versão no `app/config.py`
2. Atualize o CHANGELOG.md
3. Adicione uma tag Git:
   ```bash
   git tag -a v1.2.3 -m "Versão 1.2.3"
   git push origin v1.2.3
   ```

## Referências e Recursos

- [Documentação do FastAPI](https://fastapi.tiangolo.com/)
- [Documentação do librouteros](https://librouteros.readthedocs.io/)
- [Documentação da API MikroTik](https://wiki.mikrotik.com/wiki/Manual:API)
- [Documentação do Zabbix](https://www.zabbix.com/documentation/current/)