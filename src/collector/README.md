# TriplePlay-Sentinel Collector v2.1.0

**🆕 Agora com Redis e arquitetura ultra-simplificada!**

## 🚀 Quick Start

### 1. Configuração Básica
```bash
# Clone o projeto
git clone https://github.com/tripleplay-dev/TriplePlay-Sentinel.git
cd TriplePlay-Sentinel

# Configure o ambiente
cp .env.example .env
# Edite o .env conforme necessário
```

### 2. Deploy Simples (Apenas Collector)
```bash
# Build e start básico
docker-compose up -d

# Verificar logs
docker-compose logs -f sentinel-collector

# Verificar status
curl http://localhost:5000/api/health
```

### 3. Deploy Docker (Recomendado) ⭐
```bash
# Use o docker-compose unificado
docker-compose up -d

# Verificar status dos serviços
docker-compose ps

# Acesse:
# - Collector API: http://localhost:5000
# - Dashboard: http://localhost:5000/dashboard
```

### 4. Deploy Manual (Desenvolvimento)
```bash
cd src/collector

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis
export COLLECTOR_HOST=0.0.0.0
export COLLECTOR_PORT=5000

# Executar
python app.py
```

## 🧪 Testando o Collector

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Teste de Ping
```bash
curl -X POST http://localhost:5000/api/test \
  -H "Content-Type: application/json" \
  -d '{
    "mikrotik_host": "192.168.1.1",
    "mikrotik_user": "admin",
    "mikrotik_password": "senha",
    "test_type": "ping",
    "target": "8.8.8.8",
    "count": 4
  }'
```

### Script de Teste Automático
```bash
# Configure as credenciais no script
python test_collector.py
```

## 📊 API Endpoints

### GET /api/health
Verifica se o collector está funcionando.

**Resposta:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-22T10:30:00.123456",
  "version": "1.0.0",
  "cache_entries": 5
}
```

### POST /api/test
Executa testes de conectividade.

**Parâmetros obrigatórios:**
- `mikrotik_host`: IP do MikroTik
- `mikrotik_user`: Usuário SSH
- `mikrotik_password`: Senha SSH
- `test_type`: Tipo de teste (`ping`, `tcp_connect`, `traceroute`)
- `target`: IP/hostname de destino

**Parâmetros opcionais (ping):**
- `count`: Número de pacotes (padrão: 4)
- `size`: Tamanho do pacote (padrão: 64)
- `interval`: Intervalo entre pacotes (padrão: 1)

### GET /api/cache
Visualiza status do cache.

### DELETE /api/cache
Limpa o cache.

## 🔧 Configuração

### Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `COLLECTOR_HOST` | `0.0.0.0` | IP para bind do servidor |
| `COLLECTOR_PORT` | `5000` | Porta do servidor |
| `CACHE_TTL` | `30` | TTL do cache em segundos |
| `SSH_TIMEOUT` | `30` | Timeout SSH em segundos |
| `COMMAND_TIMEOUT` | `60` | Timeout de comandos |
| `MAX_WORKERS` | `10` | Pool de workers |
| `REQUIRE_AUTH` | `False` | Requer autenticação |
| `API_KEY` | `""` | Chave da API |

## 🐳 Docker

### Build da Imagem
```bash
cd src/collector
docker build -t tripleplay-sentinel-collector .
```

### Run Manual
```bash
docker run -d \
  --name sentinel-collector \
  -p 5000:5000 \
  -e COLLECTOR_HOST=0.0.0.0 \
  -e CACHE_TTL=30 \
  tripleplay-sentinel-collector
```

## 🔍 Troubleshooting

### Logs
```bash
# Docker
docker-compose logs -f sentinel-collector

# Manual
tail -f /var/log/sentinel-collector.log
```

### Problemas Comuns

1. **Erro de conexão SSH**
   - Verifique credenciais MikroTik
   - Confirme que SSH está habilitado
   - Teste conectividade de rede

2. **Cache não funciona**
   - Verifique logs de cache
   - Clear cache: `curl -X DELETE http://localhost:5000/api/cache`

3. **Timeout nos comandos**
   - Aumente `SSH_TIMEOUT` e `COMMAND_TIMEOUT`
   - Verifique latência de rede para MikroTik