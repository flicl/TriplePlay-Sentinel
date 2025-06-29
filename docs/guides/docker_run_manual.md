# 🐳 Guia Docker Run Manual - TriplePlay-Sentinel

Este guia mostra como executar o TriplePlay-Sentinel usando comandos `docker run -d` diretos, sem docker-compose. Esta versão utiliza a biblioteca **librouteros** para máxima performance com a API MikroTik.

## 📋 Pré-requisitos

- Docker instalado e funcionando
- Imagem `tripleplay-sentinel:latest` já construída
- MikroTik com API habilitada (porta 8728/8729)
- Acesso às portas necessárias

## ⚡ Principais Características

- ✅ **API MikroTik Nativa** - Biblioteca librouteros otimizada
- ✅ **Pool de Conexões** - Máxima performance e reutilização
- ✅ **Batch Processing** - Comandos paralelos em lote
- ✅ **SSL/TLS Support** - Conexões seguras
- ✅ **Alta Concorrência** - Suporte a 1000+ requisições simultâneas

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

### 5. Executar TriplePlay-Sentinel

```bash
docker run -d \
  --name tripleplay-sentinel-collector \
  --hostname sentinel-collector \
  --network public_network \
  --network app_network \
  --restart unless-stopped \
  --publish 58500:5000 \
  --volume /root/TriplePlay-Sentinel/logs:/app/logs \
  --env COLLECTOR_HOST=0.0.0.0 \
  --env COLLECTOR_PORT=5000 \
  --env LOG_LEVEL=INFO \
  --env REDIS_ENABLED=true \
  --env REDIS_HOST=redis \
  --env REDIS_PORT=6379 \
  --env REDIS_DB=0 \
  --env CACHE_TTL=15 \
  --env MAX_CACHE_SIZE=5000 \
  --env MAX_WORKERS=50 \
  --env MAX_CONCURRENT_HOSTS=15 \
  --env MAX_CONCURRENT_COMMANDS=200 \
  --env MAX_CONNECTIONS_PER_HOST=50 \
  --env MIKROTIK_API_TIMEOUT=30 \
  --env MIKROTIK_MAX_RETRIES=3 \
  --env REQUEST_TIMEOUT=120 \
  --env GUNICORN_WORKERS=6 \
  --env ENABLE_AUTH=true \
  --env API_KEY=k8J9mP2xQ7wN5sR1vZ3cF6hL0dA4tY8uE9iO7bG2nM1 \
  --label "com.tripleplay.service=sentinel-collector" \
  --label "com.tripleplay.version=2.1.0" \
  --health-cmd="curl -f http://localhost:5000/health || wget --no-verbose --tries=1 --spider http://localhost:5000/health" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  --health-start-period=30s \
  tripleplay-sentinel:latest
```

## � Variáveis de Ambiente Otimizadas

As seguintes variáveis foram configuradas para **alta concorrência** (1000-2000 requisições simultâneas):

### 📊 **Recursos do Container**
- `--memory="1g"` - **1GB RAM** para suportar alta carga
- `--cpus="8.0"` - **8 CPU cores** para máximo paralelismo

### 🔧 **Configurações de Concorrência**
- `MAX_CONCURRENT_HOSTS=15` - Máximo **15 MikroTiks** simultâneos
- `MAX_CONCURRENT_COMMANDS=200` - **200 comandos** por MikroTik simultaneamente  
- `MAX_CONNECTIONS_PER_HOST=50` - **50 conexões TCP** por MikroTik
- `MAX_WORKERS=50` - **50 threads** para operações paralelas

### ⚡ **Performance e Cache**
- `CACHE_TTL=15` - Cache de **15 segundos** (dados mais frescos)
- `MAX_CACHE_SIZE=5000` - Cache para **5000 resultados**
- `REQUEST_TIMEOUT=120` - **2 minutos** timeout (traceroute pode demorar)
- `MIKROTIK_API_TIMEOUT=30` - **30 segundos** timeout por comando

### 🌐 **Servidor Web (Gunicorn)**
- `GUNICORN_WORKERS=6` - **6 workers** Gunicorn para alta carga

### 🎯 **Capacidade Total:**
- ✅ **15 MikroTiks × 200 comandos = 3000 operações simultâneas**
- ✅ **50 conexões TCP por MikroTik = distribuição eficiente**
- ✅ **Suporte completo ao seu cenário de alta concorrência**

---

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

# Teste de alta concorrência - 50 IPs simultaneamente
curl -H "X-API-Key: k8J9mP2xQ7wN5sR1vZ3cF6hL0dA4tY8uE9iO7bG2nM1" \
     -H "Content-Type: application/json" \
     -d '{
       "host": "192.168.1.1",
       "username": "admin", 
       "password": "senha",
       "targets": [
         "8.8.8.8", "1.1.1.1", "8.8.4.4", "1.0.0.1",
         "9.9.9.9", "208.67.222.222", "208.67.220.220",
         "76.76.19.19", "76.76.76.76", "94.140.14.14",
         "149.112.112.112", "185.228.168.9", "185.228.169.9",
         "77.88.8.8", "77.88.8.1", "156.154.70.1",
         "156.154.71.1", "8.26.56.26", "8.20.247.20",
         "199.85.126.10", "199.85.127.10", "81.218.119.11",
         "209.244.0.3", "209.244.0.4", "195.46.39.39",
         "195.46.39.40", "69.146.16.1", "69.146.17.1",
         "216.146.35.35", "216.146.36.36", "37.235.1.174",
         "37.235.1.177", "198.101.242.72", "23.253.163.53",
         "64.6.64.6", "64.6.65.6", "84.200.69.80",
         "84.200.70.40", "8.8.8.1", "168.95.1.1",
         "168.95.192.1", "203.80.96.10", "203.80.96.9",
         "180.76.76.76", "119.29.29.29", "114.114.114.114",
         "223.5.5.5", "223.6.6.6", "117.50.11.11",
         "117.50.22.22", "101.226.4.6"
       ],
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

# Ver estatísticas de performance
curl -H "X-API-Key: k8J9mP2xQ7wN5sR1vZ3cF6hL0dA4tY8uE9iO7bG2nM1" \
     http://localhost:58500/api/v2/stats
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

*Documentação gerada para TriplePlay-Sentinel v2.2.2 (API-Only)*
