# Guia de Importação - Template Zabbix 6.0

## 📋 Pré-requisitos

Antes de importar o template, certifique-se de que:

- [x] Zabbix Server 6.0+ está instalado e funcionando
- [x] TriplePlay-Sentinel Collector está rodando
- [x] Dispositivo MikroTik está acessível via SSH
- [x] Conectividade entre Zabbix Server e Collector está funcionando

## 🔧 Processo de Importação Detalhado

### Passo 1: Download do Template

```bash
# Download do template via curl
curl -O https://raw.githubusercontent.com/seu-repo/TriplePlay-Sentinel/main/templates/zabbix/tripleplay-sentinel-template.yml

# Ou clone o repositório
git clone https://github.com/seu-repo/TriplePlay-Sentinel.git
cd TriplePlay-Sentinel/templates/zabbix/
```

### Passo 2: Validação do Template

Antes de importar, valide o formato YAML:

```bash
# Usando yq para validar
yq eval '.' tripleplay-sentinel-template.yml > /dev/null

# Ou usando python
python -c "import yaml; yaml.safe_load(open('tripleplay-sentinel-template.yml'))"
```

### Passo 3: Importação via Interface Web

1. **Acessar Zabbix Frontend**
   - URL: `http://seu-zabbix-server/zabbix`
   - Login com usuário Admin

2. **Navegar para Templates**
   ```
   Configuration → Templates
   ```

3. **Iniciar Importação**
   - Clique no botão **"Import"** (canto superior direito)
   - Clique em **"Choose File"**
   - Selecione `tripleplay-sentinel-template.yml`

4. **Configurar Opções de Importação**
   ```
   ✅ Groups
      ✅ Create new
      ✅ Update existing
   
   ✅ Templates  
      ✅ Create new
      ✅ Update existing
   
   ✅ Items
      ✅ Create new
      ✅ Update existing
   
   ✅ Triggers
      ✅ Create new
      ✅ Update existing
   
   ✅ Graphs
      ✅ Create new
      ✅ Update existing
   
   ✅ Dashboards
      ✅ Create new
      ✅ Update existing
   ```

5. **Executar Importação**
   - Clique em **"Import"**
   - Aguarde confirmação de sucesso

### Passo 4: Verificação da Importação

Verifique se os seguintes elementos foram criados:

#### Groups
- `TriplePlay-Sentinel`

#### Templates
- `TriplePlay-Sentinel Monitoring`

#### Items (principais)
- `Ping Packet Loss % to DNS1`
- `Ping Average RTT to DNS1`
- `TCP Connection Status HTTP`
- `Collector Health Status`

#### Triggers (principais)
- `Ping: Total packet loss to {$TARGET_DNS1}`
- `TriplePlay Collector: Service unhealthy`
- `MikroTik: SSH connection failed`

#### Dashboards
- `TriplePlay-Sentinel Network Monitoring`
- `TriplePlay-Sentinel Technical Dashboard`

## 🎯 Configuração de Host

### Criação do Host

```sql
-- Via SQL (opcional, para automação)
INSERT INTO hosts (hostid, host, name, status, description) 
VALUES (NULL, 'tripleplay-monitor', 'TriplePlay Network Monitor', 0, 'Monitor de rede TriplePlay-Sentinel');
```

### Via Interface Web

1. **Criar Novo Host**
   ```
   Configuration → Hosts → Create host
   ```

2. **Configurações Básicas**
   ```
   Host name: tripleplay-monitor-site1
   Visible name: TriplePlay Monitor - Site 1
   Groups: TriplePlay-Sentinel
   Interfaces: [não necessário - usa HTTP Agent]
   ```

3. **Aplicar Template**
   - Aba **"Templates"**
   - Em **"Link new templates"**: `TriplePlay-Sentinel Monitoring`
   - Clique **"Add"** → **"Update"**

## 🔧 Configuração de Macros

### Macros Obrigatórias

Configure no nível do **Host** (não global):

```yaml
# Collector Settings
{$COLLECTOR_URL}: "http://192.168.1.100:5000"
{$COLLECTOR_TIMEOUT}: "30s"

# MikroTik Settings
{$MIKROTIK_HOST}: "192.168.1.1"
{$MIKROTIK_USER}: "admin"  
{$MIKROTIK_PASSWORD}: "sua-senha-aqui"

# Test Targets
{$TARGET_DNS1}: "8.8.8.8"
{$TARGET_DNS2}: "1.1.1.1"
{$TARGET_WEB}: "www.google.com"
{$TARGET_GATEWAY}: "192.168.1.1"

# Ports
{$PORT_HTTP}: "80"
{$PORT_HTTPS}: "443"
{$PORT_DNS}: "53"
```

### Macros de Threshold (Opcionais)

```yaml
# Ping Thresholds
{$PING_LOSS_WARN}: "10"
{$PING_LOSS_HIGH}: "25"
{$PING_RTT_WARN}: "100"
{$PING_RTT_HIGH}: "200"
{$PING_JITTER_WARN}: "50"
{$PING_JITTER_HIGH}: "100"

# TCP Thresholds
{$TCP_CONNECT_TIME_WARN}: "5000"
{$TCP_CONNECT_TIME_HIGH}: "10000"

# Quality Thresholds
{$NETWORK_QUALITY_MIN}: "70"
{$PING_SUCCESS_RATE_MIN}: "95"
{$CACHE_HIT_RATE_MIN}: "70"

# Traceroute Thresholds
{$TRACEROUTE_HOPS_MAX}: "15"
{$TRACEROUTE_TIME_WARN}: "5000"

# MikroTik Thresholds
{$MIKROTIK_RESPONSE_TIME_WARN}: "3000"
```

## 🔍 Teste de Funcionamento

### Verificação Manual de Items

1. **Via Interface Web**
   ```
   Monitoring → Latest data
   Host: [seu-host]
   Filter: tripleplay
   ```

2. **Via API**
   ```bash
   # Teste direto na API do collector
   curl -X POST http://192.168.1.100:5000/api/test \
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

### Verificação de Health

```bash
# Health check do collector
curl http://192.168.1.100:5000/api/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "cache": {
    "hit_rate_percent": 85.5,
    "total_requests": 1000,
    "cache_hits": 855
  },
  "timestamp": "2025-01-22T10:30:00Z"
}
```

## 🚨 Troubleshooting da Importação

### Erro: "Cannot import template"

**Possíveis causas:**
- Formato YAML inválido
- Versão Zabbix incompatível 
- Permissões insuficientes

**Solução:**
```bash
# Validar YAML
yamllint tripleplay-sentinel-template.yml

# Verificar versão Zabbix
zabbix_server --version

# Verificar permissões do usuário
```

### Erro: "Duplicate UUID"

**Causa:** Template já foi importado anteriormente

**Solução:**
1. Delete o template existente
2. Ou use opção "Update existing" na importação

### Items ficam em estado "Not supported"

**Verificações:**
1. **Collector acessível?**
   ```bash
   curl -I http://192.168.1.100:5000/api/health
   ```

2. **Credenciais MikroTik corretas?**
   ```bash
   ssh admin@192.168.1.1 "/ip address print"
   ```

3. **Timeout suficiente?**
   - Aumente `{$COLLECTOR_TIMEOUT}` para `60s`

### Discovery Rules não funcionam

**Verificação:**
```bash
# Teste manual do endpoint de discovery
curl http://192.168.1.100:5000/api/discovery/targets
```

**Resposta esperada:**
```json
{
  "targets": [
    {
      "{#TARGET_NAME}": "Google DNS",
      "{#TARGET_IP}": "8.8.8.8",
      "{#TARGET_TYPE}": "dns"
    },
    {
      "{#TARGET_NAME}": "Cloudflare DNS", 
      "{#TARGET_IP}": "1.1.1.1",
      "{#TARGET_TYPE}": "dns"
    }
  ]
}
```

## 📊 Verificação dos Dashboards

### Dashboard Principal

1. **Acessar Dashboard**
   ```
   Monitoring → Dashboards → TriplePlay-Sentinel Network Monitoring
   ```

2. **Verificar Widgets**
   - Network Status Summary
   - DNS1/DNS2 Performance Graphs
   - TCP Services Status
   - Collector Performance

### Dashboard Técnico

```
Monitoring → Dashboards → TriplePlay-Sentinel Technical Dashboard
```

## 🔄 Importação via API (Automação)

Para ambientes automatizados:

```bash
#!/bin/bash
# import-template.sh

ZABBIX_URL="http://seu-zabbix/zabbix/api_jsonrpc.php"
USERNAME="Admin"
PASSWORD="zabbix"

# Obter token de autenticação
TOKEN=$(curl -s -X POST $ZABBIX_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {
      "user": "'$USERNAME'",
      "password": "'$PASSWORD'"
    },
    "id": 1
  }' | jq -r '.result')

# Importar template
curl -s -X POST $ZABBIX_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "configuration.import",
    "params": {
      "format": "yaml",
      "source": "'$(cat tripleplay-sentinel-template.yml | base64 -w 0)'",
      "rules": {
        "groups": {"createMissing": true, "updateExisting": true},
        "templates": {"createMissing": true, "updateExisting": true},
        "items": {"createMissing": true, "updateExisting": true},
        "triggers": {"createMissing": true, "updateExisting": true}
      }
    },
    "auth": "'$TOKEN'",
    "id": 2
  }'
```

## ✅ Checklist Final

Após importação bem-sucedida:

- [ ] Template aparece em Configuration → Templates
- [ ] Group "TriplePlay-Sentinel" foi criado
- [ ] Items estão coletando dados (não "No data")
- [ ] Triggers estão funcionando (não "Unknown")
- [ ] Dashboards são exibidos corretamente
- [ ] Discovery rules estão criando items automaticamente
- [ ] Macros estão configuradas no host
- [ ] Collector está respondendo às requisições

---

**Próximos passos:** [Configuração de Hosts](host-configuration.md)