# Sentinel Collector

O Sentinel Collector é o componente central do sistema Sentinel, atuando como intermediário entre o Zabbix e os roteadores MikroTik para monitoramento de conectividade de rede.

## Funcionalidades

- Recebe requisições do Zabbix via HTTP/HTTPS
- Conecta aos dispositivos MikroTik usando SSH/API
- Executa testes de conectividade (ping, TCP connect, traceroute)
- Processa e retorna resultados estruturados no formato JSON
- Oferece um dashboard web para execução manual de testes
- Suporta criptografia de credenciais sensíveis
- Implementa sistema de cache para otimizar o desempenho
- Suporta múltiplas requisições concorrentes
- Logging detalhado para troubleshooting
- Mecanismo aprimorado de configuração com fallback
- Sistema de retry para conexões MikroTik
- Suporte a CORS para integração com outras aplicações

## Dashboard Web

O coletor inclui um dashboard web completo para execução manual de testes, permitindo:

- Executar testes de ping, TCP connect e traceroute
- Visualizar resultados em formato amigável
- Acompanhar histórico dos últimos testes realizados
- Verificar estatísticas do coletor

Para acessar o dashboard, basta navegar para a URL do coletor (ex: http://localhost:5000/).

## Endpoints da API

### GET /api/health
Verifica o status de operação do coletor.

**Resposta:**
```json
{
    "status": "operational",
    "timestamp": "2025-05-10T15:30:00.123456",
    "version": "1.0.0",
    "uptime": 3600
}
```

### GET /api/version
Retorna informações de versão do coletor.

**Resposta:**
```json
{
    "name": "Sentinel Collector",
    "version": "1.0.0",
    "description": "Componente central do Sistema Sentinel para monitoramento via MikroTik-Zabbix",
    "author": "TriplePlay Team"
}
```

### GET /api/stats
Retorna estatísticas de uso do coletor.

**Resposta:**
```json
{
    "timestamp": "2025-05-10T15:30:00.123456",
    "uptime": 3600,
    "cache": {
        "enabled": true,
        "ttl": 300,
        "size": 5,
        "items": [
            {
                "key": "ping:8.8.8.8:count=3;size=64",
                "test_type": "ping",
                "target": "8.8.8.8",
                "age_seconds": 120,
                "timestamp": "2025-05-10T15:28:00.123456"
            }
        ]
    }
}
```

### POST /api/test
Executa um teste de conectividade a partir de um dispositivo MikroTik.

**Requisição:**
```json
{
    "mikrotik_host": "192.168.1.1",
    "mikrotik_user": "admin",                // Opcional se configurado no servidor
    "mikrotik_password": "password",         // Opcional se configurado no servidor
    "test_type": "ping",                     // "ping", "tcp" ou "traceroute"
    "target": "8.8.8.8",
    "count": 3,                              // Para ping (opcional)
    "size": 64,                              // Para ping (opcional)
    "port": 80,                              // Para tcp (opcional)
    "max_hops": 30,                          // Para traceroute (opcional)
    "use_cache": true                        // Opcional (padrão: true)
}
```

**Resposta para teste de ping:**
```json
{
    "status": "success",
    "ping_stats": {
        "sent": 3,
        "received": 3,
        "packet_loss": 0,
        "min_rtt": 10.5,
        "avg_rtt": 12.3,
        "max_rtt": 15.7
    },
    "metadata": {
        "timestamp": "2025-05-10T15:30:00.123456",
        "test_type": "ping",
        "target": "8.8.8.8",
        "mikrotik_host": "192.168.1.1"
    }
}
```

**Resposta para teste de conexão TCP:**
```json
{
    "status": "success",
    "tcp_test": {
        "reachable": true,
        "target": "8.8.8.8",
        "port": 80,
        "message": "Conexão TCP estabelecida com sucesso"
    },
    "metadata": {
        "timestamp": "2025-05-10T15:30:00.123456",
        "test_type": "tcp",
        "target": "8.8.8.8",
        "mikrotik_host": "192.168.1.1"
    }
}
```

**Resposta para teste de traceroute:**
```json
{
    "status": "success",
    "traceroute": {
        "hops": [
            {
                "hop": 1,
                "ip": "192.168.1.1",
                "unreachable": false,
                "rtt": 1.5,
                "rtt_samples": [1.5]
            },
            {
                "hop": 2,
                "ip": "200.150.100.1",
                "unreachable": false,
                "rtt": 15.3,
                "rtt_samples": [15.3]
            }
        ],
        "hop_count": 2,
        "target_reached": true
    },
    "metadata": {
        "timestamp": "2025-05-10T15:30:00.123456",
        "test_type": "traceroute",
        "target": "8.8.8.8",
        "mikrotik_host": "192.168.1.1"
    }
}
```

## Configuração

A configuração do coletor pode ser feita através de:

1. Variáveis de ambiente
2. Arquivo .env no diretório do coletor
3. Arquivo de configuração JSON (configurável via variável CONFIG_FILE)

Veja o arquivo `.env.example` para todas as opções de configuração disponíveis.

### Configurações Principais

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| HOST | Endereço IP para bind do servidor | 0.0.0.0 |
| PORT | Porta para bind do servidor | 5000 |
| DEBUG_MODE | Habilita modo de debug | False |
| MIKROTIK_USER | Usuário padrão para MikroTik | - |
| MIKROTIK_PASSWORD | Senha padrão para MikroTik | - |
| MIKROTIK_TIMEOUT | Timeout para conexão com MikroTik (segundos) | 10 |
| MIKROTIK_RETRY_COUNT | Número de tentativas de reconexão | 2 |
| CACHE_ENABLED | Habilita cache de resultados | True |
| CACHE_TTL | Tempo de vida do cache em segundos | 300 |
| ENABLE_ENCRYPTION | Habilita criptografia de credenciais | False |
| ENCRYPTION_KEY | Chave para criptografia | - |
| LOG_LEVEL | Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL) | INFO |
| LOG_FILE | Arquivo de log | logs/collector.log |

### Segurança

Para habilitar HTTPS, configure as seguintes variáveis:

```
SSL_CERT_PATH=/caminho/para/certificado.pem
SSL_KEY_PATH=/caminho/para/chave.key
```

Para habilitar criptografia de credenciais:

```
ENABLE_ENCRYPTION=True
ENCRYPTION_KEY=sua_chave_secreta_aqui
```

## Executando Localmente

```bash
# Criar ambiente virtual (se ainda não existir)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
nano .env

# Executar o collector
python collector.py
```

## Executando com Docker

```bash
# Construir e iniciar o container
docker build -t sentinel-collector .
docker run -p 5000:5000 -v $(pwd)/.env:/app/.env sentinel-collector
```

Com Docker Compose:

```bash
docker-compose up -d
```

## Testando o Collector

Use o script de teste fornecido:

```bash
python ../scripts/test_collector.py --mikrotik 192.168.88.1 --user admin --password sua_senha --target 8.8.8.8
```

Ou use curl para testes manuais:

```bash
# Verificar saúde
curl http://localhost:5000/api/health

# Executar teste de ping
curl -X POST http://localhost:5000/api/test \
  -H "Content-Type: application/json" \
  -d '{"mikrotik_host":"192.168.88.1","mikrotik_user":"admin","mikrotik_password":"password","test_type":"ping","target":"8.8.8.8","count":3}'

# Executar teste de traceroute
curl -X POST http://localhost:5000/api/test \
  -H "Content-Type: application/json" \
  -d '{"mikrotik_host":"192.168.88.1","mikrotik_user":"admin","mikrotik_password":"password","test_type":"traceroute","target":"8.8.8.8","max_hops":30}'
```

## Sistema de Configuração Avançado

O Sentinel Collector agora conta com um sistema de configuração robusto que suporta:

1. **Configuração em camadas**: 
   - Variáveis de ambiente (maior prioridade)
   - Arquivos de configuração JSON (média prioridade)
   - Valores padrão (menor prioridade)

2. **`ConfigManager`**: Uma classe com funcionalidades avançadas
   - Acesso a configurações aninhadas (notação com pontos)
   - Validação automática de configurações
   - Criptografia de dados sensíveis

3. **`config_helper.py`**: Um módulo de compatibilidade que:
   - Tenta usar o `ConfigManager` avançado quando disponível
   - Inclui um fallback para configuração simples via variáveis de ambiente
   - Garante que a aplicação funcione mesmo sem o sistema avançado

### Uso do ConfigManager

Em código Python, use o ConfigManager assim:

```python
# Importar o config_helper que gerencia o fallback
from config_helper import config

# Acessar uma configuração com valor padrão
timeout = config.get('server.timeout', 5)

# Acessar um nível de log formatado para o logging
log_level = config.get_log_level()

# Obter todas as configurações do servidor
server_config = config.get_server_settings()
```

### Arquivo de Configuração

Para usar um arquivo de configuração, crie um JSON com a estrutura:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false,
    "timeout": 5,
    "ssl_cert": "",
    "ssl_key": ""
  },
  "security": {
    "enable_encryption": false,
    "encryption_key": "",
    "salt": ""
  },
  "mikrotik": {
    "default_user": "admin",
    "default_password": "password",
    "connection_timeout": 10,
    "retry_count": 2
  },
  "cache": {
    "enabled": true,
    "ttl": 300
  },
  "logging": {
    "level": "INFO",
    "file": "logs/collector.log"
  }
}
```

Salve como `config/config.json` para uso automatizado.
