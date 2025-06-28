# 🐳 Guia Docker Run Manual - TriplePlay-Sentinel (API-Only)

Este guia mostra como executar o TriplePlay-Sentinel usando comandos `docker run -d` diretos, sem docker-compose. Esta versão utiliza **100% API MikroTik** com a biblioteca **librouteros**, eliminando completamente o SSH.

## 📋 Pré-requisitos

- Docker instalado e funcionando
- Imagem `tripleplay-sentinel:latest` já construída
- MikroTik com API habilitada (porta 8728/8729)
- Acesso às portas necessárias

## ⚡ Principais Mudanças (API-Only)

- ✅ **100% API MikroTik** - Sem SSH
- ✅ **librouteros** - Biblioteca nativa e otimizada  
- ✅ **Pool de Conexões** - Máxima performance
- ✅ **Batch Processing** - Comandos em lote
- ✅ **SSL/TLS Support** - Conexões seguras
- ❌ **Sem SSH** - Dependências removidas

## 🏗️ Arquitetura de Rede

O projeto utiliza duas redes separadas para segurança:

- **app_network** (172.20.1.0/24): Rede interna para comunicação Redis
- **public_network** (172.20.2.0/24): Rede externa para acesso ao Sentinel

## 🚀 Passo a Passo


### 1. Criar Volumes

```bash
# Volume para dados do Redis
docker volume create redis_data

# Criar diretório para logs
mkdir -p /root/TriplePlay-Sentinel/logs
```

### 2. Criar Redes Docker

```bash
# Criar rede interna
docker network create --driver bridge \
  --subnet=172.20.1.0/24 \
  --gateway=172.20.1.1 \
  app_network

# Criar rede externa  
docker network create --driver bridge \
  --subnet=172.20.2.0/24 \
  --gateway=172.20.2.1 \
  public_network
```

### 3. Executar Redis

```bash
docker run -d \
  --name tripleplay-redis \
  --hostname redis \
  --network app_network \
  --restart unless-stopped \
  --memory="256m" \
  --cpus="1" \
  --volume redis_data:/data \
  --label "com.tripleplay.service=redis-cache" \
  --health-cmd="redis-cli ping" \
  --health-interval=10s \
  --health-timeout=5s \
  --health-retries=3 \
  redis:7-alpine \
  redis-server \
  --appendonly yes \
  --appendfsync everysec \
  --maxmemory 256mb \
  --maxmemory-policy allkeys-lru
```

### 4. Aguardar Redis Ficar Healthy

```bash
# Verificar status do Redis
docker ps
docker logs tripleplay-redis

# Aguardar até o health check passar
docker inspect tripleplay-redis --format='{{.State.Health.Status}}'
```

### 5. Executar TriplePlay-Sentinel (API-Only)

```bash
docker run -d \
  --name tripleplay-sentinel-collector \
  --hostname sentinel-collector \
  --network public_network \
  --network app_network \
  --restart unless-stopped \
  --memory="512m" \
  --cpus="4.0" \
  --publish 58500:5000 \
  --volume /root/TriplePlay-Sentinel/logs:/app/logs \
  --env COLLECTOR_HOST=0.0.0.0 \
  --env COLLECTOR_PORT=5000 \
  --env LOG_LEVEL=INFO \
  --env REDIS_ENABLED=true \
  --env REDIS_HOST=redis \
  --env REDIS_PORT=6379 \
  --env REDIS_DB=0 \
  --env CACHE_TTL=30 \
  --env MAX_WORKERS=10 \
  --env REQUEST_TIMEOUT=60 \
  --env ENABLE_AUTH=true \
  --env API_KEY=k8J9mP2xQ7wN5sR1vZ3cF6hL0dA4tY8uE9iO7bG2nM1 \
  --label "com.tripleplay.service=sentinel-collector" \
  --label "com.tripleplay.version=2.1.0" \
  --health-cmd="curl -f http://localhost:5000/health" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  --health-start-period=30s \
  tripleplay-sentinel:latest
```

## 🔑 Gerando API Key (Opcional)

Se você quiser habilitar autenticação na API, precisa gerar uma chave segura primeiro:

### Opção 1 - OpenSSL (Recomendado)
```bash
# Gerar chave aleatória de 32 bytes em base64
openssl rand -base64 32
```

### Opção 2 - Python
```bash
# Gerar chave usando Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Opção 3 - Manual
```bash
# Gerar chave usando /dev/urandom
cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1
```

### 💡 Exemplo de saída:
```
k8J9mP2xQ7wN5sR1vZ3cF6hL0dA4tY8uE9iO7bG2nM1
```

### 🔒 Como usar:
1. Execute um dos comandos acima
2. Copie a chave gerada
3. Substitua `sua_chave_secreta_aqui` pela chave real no comando docker run

**⚠️ Importante:**
- Guarde a chave em local seguro
- Não compartilhe a chave em logs ou repositórios
- Use chaves diferentes para cada ambiente (dev, prod)

## 🔍 Verificação

### Verificar Containers Rodando

```bash
docker ps
```

### Verificar Logs

```bash
# Logs do Redis
docker logs tripleplay-redis

# Logs do Sentinel
docker logs tripleplay-sentinel-collector
```

### Verificar Redes

```bash
# Listar redes
docker network ls

# Inspecionar rede interna
docker network inspect tripleplay-app-network

# Inspecionar rede externa
docker network inspect tripleplay-public-network
```

### Testar Conectividade

```bash
# Testar Redis dentro do container sentinel
docker exec tripleplay-sentinel-collector redis-cli -h redis ping

# Testar API do Sentinel
curl http://localhost:58500/api/health
```

### Testar API com Autenticação

Se você habilitou autenticação (`ENABLE_AUTH=true`):

```bash
# Opção 1 - Bearer Token
curl -H "Authorization: Bearer sua_chave_secreta_aqui" \
     http://localhost:58500/api/health

# Opção 2 - X-API-Key Header  
curl -H "X-API-Key: sua_chave_secreta_aqui" \
     http://localhost:58500/api/health

### Testar API MikroTik

```bash
# Ping via API MikroTik (porta padrão 8728)
curl -H "X-API-Key: k8J9mP2xQ7wN5sR1vZ3cF6hL0dA4tY8uE9iO7bG2nM1" \
     -H "Content-Type: application/json" \
     -d '{
       "host": "192.168.1.1",
       "username": "admin", 
       "password": "senha",
       "targets": ["8.8.8.8", "1.1.1.1"],
       "count": 4
     }' \
     http://localhost:58500/api/v2/mikrotik/ping

# Ping via API MikroTik (porta customizada)
curl -H "X-API-Key: k8J9mP2xQ7wN5sR1vZ3cF6hL0dA4tY8uE9iO7bG2nM1" \
     -H "Content-Type: application/json" \
     -d '{
       "host": "192.168.1.1",
       "username": "admin", 
       "password": "senha",
       "port": 8729,
       "use_ssl": true,
       "targets": ["8.8.8.8", "1.1.1.1"],
       "count": 4
     }' \
     http://localhost:58500/api/v2/mikrotik/ping

# Comando MikroTik via API (porta customizada)
curl -H "X-API-Key: k8J9mP2xQ7wN5sR1vZ3cF6hL0dA4tY8uE9iO7bG2nM1" \
     -H "Content-Type: application/json" \
     -d '{
       "host": "192.168.1.1",
       "username": "admin",
       "password": "senha",
       "port": 8729,
       "use_ssl": true,
       "command": "/system/identity/print",
       "parameters": {}
     }' \
     http://localhost:58500/api/v2/mikrotik/command

# Testar conectividade com porta customizada
curl -H "X-API-Key: k8J9mP2xQ7wN5sR1vZ3cF6hL0dA4tY8uE9iO7bG2nM1" \
     -H "Content-Type: application/json" \
     -d '{
       "host": "192.168.1.1",
       "username": "admin",
       "password": "senha",
       "port": 8729,
       "use_ssl": true
     }' \
     http://localhost:58500/api/v2/test-connection
```
```

### Testar API sem Autenticação

Se autenticação estiver desabilitada (`ENABLE_AUTH=false`):

```bash
# Health check público
curl http://localhost:58500/api/health

# Dashboard público
curl http://localhost:58500/
```

## 🛑 Parar e Limpar

### Parar Containers

```bash
docker stop tripleplay-sentinel-collector tripleplay-redis
```

### Remover Containers

```bash
docker rm tripleplay-sentinel-collector tripleplay-redis
```

### Limpar Redes

```bash
docker network rm tripleplay-app-network tripleplay-public-network
```

### Limpar Volumes (Opcional)

```bash
docker volume rm redis_data
```

## 📊 Monitoramento

### Status dos Containers

```bash
# Ver status geral
docker stats

# Ver health checks
docker inspect tripleplay-redis --format='{{.State.Health.Status}}'
docker inspect tripleplay-sentinel-collector --format='{{.State.Health.Status}}'
```

### Acesso ao Dashboard

Após inicialização completa:
- **URL**: http://localhost:58500
- **API Health**: http://localhost:58500/api/health

## 🔧 Troubleshooting

### Problema: Redis não conecta
```bash
# Verificar se Redis está rodando
docker logs tripleplay-redis

# Testar conectividade
docker exec tripleplay-sentinel-collector ping redis
```

### Problema: Porta já em uso
```bash
# Verificar processos usando a porta
netstat -tulpn | grep 58500

# Usar porta alternativa
# Alterar --publish 58501:5000
```

### Problema: Memória insuficiente
```bash
# Verificar uso de memória
docker stats

# Reduzir limites se necessário
# --memory="256m" para o sentinel
```

## � Configuração de Porta MikroTik

**Importante:** A porta da API MikroTik é especificada **no request**, não como variável de ambiente. Isso permite conectar a diferentes MikroTiks com portas diferentes:

### ✅ Correto: Porta no Request
```json
{
  "host": "192.168.1.1",
  "username": "admin",
  "password": "senha",
  "port": 8729,          // ← Porta específica para este MikroTik
  "use_ssl": true,
  "targets": ["8.8.8.8"]
}
```

### ❌ Incorreto: Porta como ENV (inflexível)
```bash
# Não faça isso - limita a um tipo de configuração
--env MIKROTIK_API_PORT=8728
```

### 🎯 Benefícios dessa Abordagem:
- **Flexibilidade**: Cada MikroTik pode usar porta diferente
- **Multi-tenant**: Suporte a redes com configurações variadas  
- **Compatibilidade**: Funciona com HTTP (8728) e HTTPS (8729)
- **Dinâmico**: Sem necessidade de restart para diferentes portas

## �📝 Notas Importantes (API-Only)

1. **API MikroTik**: Configure a API no MikroTik: `/ip service enable api`
2. **Porta API**: Especificada por request - 8728 (HTTP) ou 8729 (HTTPS) 
3. **librouteros**: Biblioteca nativa Python para máxima performance
4. **Pool de Conexões**: Reutiliza conexões para eficiência
5. **Sem SSH**: Zero dependências SSH, mais seguro e rápido
6. **SSL/TLS**: Suporte nativo para conexões seguras
7. **Batch**: Processa múltiplos comandos simultaneamente

### 🔧 Configuração MikroTik

```bash
# Habilitar API no MikroTik
/ip service enable api
/ip service set api port=8728

# Para SSL (recomendado produção)  
/ip service enable api-ssl
/ip service set api-ssl port=8729
```

---

*Documentação gerada para TriplePlay-Sentinel v2.1.0 (API-Only)*
