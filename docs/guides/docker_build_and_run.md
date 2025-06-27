# 🐳 Guia de Build e Execução Docker - TriplePlay-Sentinel

Este guia mostra como criar a imagem Docker e executar o container do TriplePlay-Sentinel usando comandos `docker build` e `docker run`.

## 📋 Pré-requisitos

- Docker Engine 20.10+ instalado
- Git para clonar o repositório
- Acesso à internet para download das dependências

## 🔧 Preparação do Ambiente

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/TriplePlay-Sentinel.git
cd TriplePlay-Sentinel
```

### 2. Verifique os Arquivos Necessários

Certifique-se de que os seguintes arquivos estão presentes:

```bash
ls -la src/collector/
# Deve mostrar:
# - Dockerfile
# - requirements.txt
# - app.py
# - config.py
# - mikrotik.py
# - cache.py
# - processor.py
# - models.py
# - start.sh
```

## 🏗️ Build da Imagem Docker

### 1. Navegue até o diretório do collector

```bash
cd src/collector
```

### 2. Construa a imagem Docker

```bash
# Build básico
docker build -t tripleplay-sentinel:latest .

# Build com tag específica
docker build -t tripleplay-sentinel:v2.1.0 .

# Build com argumentos customizados
docker build \
  --build-arg DEBIAN_FRONTEND=noninteractive \
  -t tripleplay-sentinel:latest \
  .
```

### 3. Verifique se a imagem foi criada

```bash
docker images | grep tripleplay-sentinel
```

Saída esperada:
```
tripleplay-sentinel   latest    abc123def456   2 minutes ago   245MB
```

## 🚀 Execução do Container

### 1. Execução Básica (Standalone)

```bash
# Execução simples em background
docker run -d \
  --name tripleplay-sentinel \
  -p 5000:5000 \
  tripleplay-sentinel:latest

# Execução com variáveis de ambiente
docker run -d \
  --name tripleplay-sentinel \
  -p 5000:5000 \
  -e COLLECTOR_HOST=0.0.0.0 \
  -e COLLECTOR_PORT=5000 \
  -e LOG_LEVEL=INFO \
  tripleplay-sentinel:latest
```

### 2. Execução com Redis (Recomendado)

#### Primeiro, execute um container Redis:

```bash
# Criar rede Docker
docker network create tripleplay-network

# Executar Redis
docker run -d \
  --name tripleplay-redis \
  --network tripleplay-network \
  -p 6379:6379 \
  redis:7-alpine
```

#### Depois, execute o TriplePlay-Sentinel:

```bash
docker run -d \
  --name tripleplay-sentinel \
  --network tripleplay-network \
  -p 5000:5000 \
  -e COLLECTOR_HOST=0.0.0.0 \
  -e COLLECTOR_PORT=5000 \
  -e LOG_LEVEL=INFO \
  -e REDIS_ENABLED=true \
  -e REDIS_HOST=tripleplay-redis \
  -e REDIS_PORT=6379 \
  -e REDIS_DB=0 \
  -e CACHE_TTL=30 \
  -e SSH_TIMEOUT=30 \
  -e SSH_MAX_RETRIES=3 \
  -e MAX_WORKERS=10 \
  -e REQUEST_TIMEOUT=60 \
  tripleplay-sentinel:latest
```

### 3. Execução com Volume para Logs

```bash
# Criar diretório para logs
mkdir -p /opt/tripleplay-sentinel/logs

# Executar com volume montado
docker run -d \
  --name tripleplay-sentinel \
  --network tripleplay-network \
  -p 5000:5000 \
  -v /opt/tripleplay-sentinel/logs:/app/logs \
  -e COLLECTOR_HOST=0.0.0.0 \
  -e COLLECTOR_PORT=5000 \
  -e LOG_LEVEL=INFO \
  -e REDIS_ENABLED=true \
  -e REDIS_HOST=tripleplay-redis \
  -e REDIS_PORT=6379 \
  tripleplay-sentinel:latest
```

### 4. Execução Completa com Todas as Configurações

```bash
docker run -d \
  --name tripleplay-sentinel \
  --network tripleplay-network \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /opt/tripleplay-sentinel/logs:/app/logs \
  -e COLLECTOR_HOST=0.0.0.0 \
  -e COLLECTOR_PORT=5000 \
  -e LOG_LEVEL=INFO \
  -e REDIS_ENABLED=true \
  -e REDIS_HOST=tripleplay-redis \
  -e REDIS_PORT=6379 \
  -e REDIS_DB=0 \
  -e REDIS_PASSWORD="" \
  -e CACHE_TTL=30 \
  -e SSH_TIMEOUT=30 \
  -e SSH_MAX_RETRIES=3 \
  -e MAX_WORKERS=10 \
  -e REQUEST_TIMEOUT=60 \
  -e ENABLE_AUTH=false \
  -e API_KEY="" \
  tripleplay-sentinel:latest
```

## 🔍 Verificação e Monitoramento

### 1. Verificar Status dos Containers

```bash
# Listar containers em execução
docker ps

# Verificar logs do container
docker logs tripleplay-sentinel

# Seguir logs em tempo real
docker logs -f tripleplay-sentinel
```

### 2. Testar a API

```bash
# Teste de health check
curl http://localhost:5000/health

# Teste de status
curl http://localhost:5000/status

# Teste de ping (exemplo)
curl "http://localhost:5000/ping?router_ip=192.168.1.1&router_user=admin&router_pass=password&target_ip=8.8.8.8"
```

### 3. Acessar Dashboard Web

Abra o navegador e acesse:
```
http://localhost:5000
```

## ⚙️ Variáveis de Ambiente Disponíveis

| Variável | Padrão | Descrição |
|----------|---------|-----------|
| `COLLECTOR_HOST` | `0.0.0.0` | IP do servidor |
| `COLLECTOR_PORT` | `5000` | Porta do servidor |
| `LOG_LEVEL` | `INFO` | Nível de log (DEBUG, INFO, WARNING, ERROR) |
| `REDIS_ENABLED` | `false` | Habilitar cache Redis |
| `REDIS_HOST` | `localhost` | Host do Redis |
| `REDIS_PORT` | `6379` | Porta do Redis |
| `REDIS_DB` | `0` | Banco de dados Redis |
| `REDIS_PASSWORD` | `""` | Senha do Redis |
| `CACHE_TTL` | `30` | TTL do cache em segundos |
| `SSH_TIMEOUT` | `30` | Timeout SSH em segundos |
| `SSH_MAX_RETRIES` | `3` | Máximo de tentativas SSH |
| `MAX_WORKERS` | `10` | Máximo de workers simultâneos |
| `REQUEST_TIMEOUT` | `60` | Timeout de requisição em segundos |
| `ENABLE_AUTH` | `false` | Habilitar autenticação |
| `API_KEY` | `""` | Chave da API |

## 🛠️ Comandos de Gerenciamento

### Parar o Container

```bash
docker stop tripleplay-sentinel
```

### Reiniciar o Container

```bash
docker restart tripleplay-sentinel
```

### Remover o Container

```bash
docker rm tripleplay-sentinel
```

### Remover a Imagem

```bash
docker rmi tripleplay-sentinel:latest
```

### Limpar Recursos Docker

```bash
# Remover containers parados
docker container prune

# Remover imagens não utilizadas
docker image prune

# Remover tudo não utilizado
docker system prune
```

## 🔧 Troubleshooting

### 1. Container não inicia

```bash
# Verificar logs detalhados
docker logs tripleplay-sentinel

# Executar em modo interativo para debug
docker run -it --rm tripleplay-sentinel:latest bash
```

### 2. Problemas de conectividade

```bash
# Verificar redes Docker
docker network ls

# Inspecionar rede
docker network inspect tripleplay-network

# Testar conectividade entre containers
docker exec tripleplay-sentinel ping tripleplay-redis
```

### 3. Problemas de permissão

```bash
# Verificar permissões do diretório de logs
ls -la /opt/tripleplay-sentinel/logs

# Ajustar permissões se necessário
sudo chown -R 1000:1000 /opt/tripleplay-sentinel/logs
```

## 📝 Exemplos de Uso Completos

### Exemplo 1: Ambiente de Desenvolvimento

```bash
# Build da imagem
cd src/collector
docker build -t tripleplay-sentinel:dev .

# Executar em modo desenvolvimento
docker run -d \
  --name tripleplay-dev \
  -p 5000:5000 \
  -e LOG_LEVEL=DEBUG \
  tripleplay-sentinel:dev
```

### Exemplo 2: Ambiente de Produção

```bash
# Build da imagem de produção
docker build -t tripleplay-sentinel:prod .

# Criar rede
docker network create tripleplay-prod

# Redis
docker run -d \
  --name redis-prod \
  --network tripleplay-prod \
  --restart unless-stopped \
  redis:7-alpine

# TriplePlay-Sentinel
docker run -d \
  --name tripleplay-prod \
  --network tripleplay-prod \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /opt/tripleplay/logs:/app/logs \
  -e REDIS_ENABLED=true \
  -e REDIS_HOST=redis-prod \
  -e LOG_LEVEL=INFO \
  tripleplay-sentinel:prod
```

## 📚 Próximos Passos

- Para deploy em produção, considere usar [Docker Compose](docker_setup.md)
- Configure o [Zabbix](../zabbix/ZABBIX_CONFIGURATION.md) para usar o collector
- Consulte o [guia de setup do MikroTik](mikrotik_setup.md)
- Veja exemplos de [templates Zabbix](../../templates/zabbix/)

---

**📧 Suporte:** Para dúvidas ou problemas, consulte nossa [documentação completa](../INDEX.md) ou abra uma issue no repositório.
