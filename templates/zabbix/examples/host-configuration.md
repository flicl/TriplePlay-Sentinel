# Configuração de Hosts - TriplePlay-Sentinel

## 📋 Visão Geral

Este guia detalha como configurar hosts no Zabbix para usar o template TriplePlay-Sentinel. Cada host representa um site/localização que será monitorada através de um dispositivo MikroTik.

## 🏗️ Arquitetura de Hosts

### Cenário Típico

```
Zabbix Server
    ↓ HTTP Requests
TriplePlay Collector
    ↓ SSH Connections
MikroTik Site 1 → Internet Tests
MikroTik Site 2 → Internet Tests
MikroTik Site 3 → Internet Tests
```

### Estrutura Recomendada

```
Host Groups:
├── TriplePlay-Sentinel
│   ├── TriplePlay-Matriz
│   ├── TriplePlay-Filial-SP
│   ├── TriplePlay-Filial-RJ
│   └── TriplePlay-Datacenter
```

## 🎯 Configuração de Host Individual

### Passo 1: Criar Host Base

```yaml
# Configurações básicas do host
Host name: tripleplay-site1
Visible name: TriplePlay - Matriz São Paulo
Groups: TriplePlay-Sentinel
Description: Monitoramento de rede via MikroTik 192.168.1.1
Status: Enabled
```

### Passo 2: Configuração de Interfaces

**IMPORTANTE:** Para este template, não são necessárias interfaces tradicionais, pois todos os items usam HTTP Agent que faz requisições para o Collector.

```yaml
# Opcional - para referência
Agent interfaces: None
SNMP interfaces: None
JMX interfaces: None
IPMI interfaces: None
```

### Passo 3: Aplicar Template

1. Aba **Templates**
2. Link new templates: `TriplePlay-Sentinel Monitoring`
3. Add → Update

### Passo 4: Configurar Macros

#### Macros Obrigatórias

```yaml
# Collector Configuration
{$COLLECTOR_URL}: "http://10.0.0.100:5000"
{$COLLECTOR_TIMEOUT}: "30s"

# MikroTik Device
{$MIKROTIK_HOST}: "192.168.1.1"
{$MIKROTIK_USER}: "monitor"
{$MIKROTIK_PASSWORD}: "senha_segura_123"

# Test Targets - Customize conforme necessário
{$TARGET_DNS1}: "8.8.8.8"          # Google DNS
{$TARGET_DNS2}: "1.1.1.1"          # Cloudflare DNS  
{$TARGET_WEB}: "www.google.com"     # Site para teste TCP
{$TARGET_GATEWAY}: "192.168.1.1"    # Gateway local

# Network Ports
{$PORT_HTTP}: "80"
{$PORT_HTTPS}: "443"
{$PORT_DNS}: "53"
```

## 🏢 Configuração Multi-Site

### Cenário: 3 Filiais + Matriz

#### Site 1 - Matriz

```yaml
Host: tripleplay-matriz
Macros:
  {$COLLECTOR_URL}: "http://collector.empresa.com:5000"
  {$MIKROTIK_HOST}: "192.168.1.1" 
  {$MIKROTIK_USER}: "zabbix"
  {$MIKROTIK_PASSWORD}: "senha_matriz"
  {$TARGET_DNS1}: "8.8.8.8"
  {$TARGET_DNS2}: "1.1.1.1"
  {$TARGET_WEB}: "www.empresa.com"
  {$TARGET_GATEWAY}: "192.168.1.1"
```

#### Site 2 - Filial SP

```yaml
Host: tripleplay-filial-sp
Macros:
  {$COLLECTOR_URL}: "http://collector.empresa.com:5000"
  {$MIKROTIK_HOST}: "10.1.1.1"
  {$MIKROTIK_USER}: "zabbix"
  {$MIKROTIK_PASSWORD}: "senha_filial_sp"
  {$TARGET_DNS1}: "8.8.8.8"
  {$TARGET_DNS2}: "1.1.1.1"
  {$TARGET_WEB}: "www.empresa.com"
  {$TARGET_GATEWAY}: "10.1.1.1"
```

#### Site 3 - Filial RJ

```yaml
Host: tripleplay-filial-rj
Macros:
  {$COLLECTOR_URL}: "http://collector.empresa.com:5000"
  {$MIKROTIK_HOST}: "10.2.1.1"
  {$MIKROTIK_USER}: "zabbix"
  {$MIKROTIK_PASSWORD}: "senha_filial_rj"
  {$TARGET_DNS1}: "8.8.8.8"
  {$TARGET_DNS2}: "1.1.1.1"
  {$TARGET_WEB}: "www.empresa.com"
  {$TARGET_GATEWAY}: "10.2.1.1"
```

## 🔧 Configurações Avançadas

### Thresholds Personalizados por Site

Alguns sites podem ter requisitos diferentes:

#### Site com Link Dedicado (mais rigoroso)

```yaml
{$PING_LOSS_WARN}: "5"     # Default: 10
{$PING_LOSS_HIGH}: "15"    # Default: 25
{$PING_RTT_WARN}: "50"     # Default: 100
{$PING_RTT_HIGH}: "100"    # Default: 200
```

#### Site com Link Satélite (mais flexível)

```yaml
{$PING_LOSS_WARN}: "20"    # Default: 10
{$PING_LOSS_HIGH}: "40"    # Default: 25
{$PING_RTT_WARN}: "200"    # Default: 100
{$PING_RTT_HIGH}: "500"    # Default: 200
```

### Targets Customizados por Site

#### Site com Servidor Local

```yaml
{$TARGET_DNS1}: "8.8.8.8"
{$TARGET_DNS2}: "192.168.1.10"      # DNS interno
{$TARGET_WEB}: "servidor.local"      # Servidor interno
{$TARGET_GATEWAY}: "192.168.1.1"
```

#### Site com Múltiplos Links

```yaml
{$TARGET_DNS1}: "8.8.8.8"           # Link 1
{$TARGET_DNS2}: "1.1.1.1"           # Link 2
{$TARGET_WEB}: "www.google.com"
{$TARGET_GATEWAY}: "192.168.1.1"
```

## 🚀 Automação com Scripts

### Script de Criação em Massa

```bash
#!/bin/bash
# create-hosts.sh

ZABBIX_URL="http://zabbix.empresa.com/api_jsonrpc.php"
USERNAME="Admin"
PASSWORD="zabbix"

# Sites para criar
declare -A SITES=(
    ["tripleplay-matriz"]="192.168.1.1"
    ["tripleplay-filial-sp"]="10.1.1.1"
    ["tripleplay-filial-rj"]="10.2.1.1"
    ["tripleplay-datacenter"]="172.16.1.1"
)

# Função para autenticação
get_token() {
    curl -s -X POST $ZABBIX_URL \
        -H "Content-Type: application/json" \
        -d '{
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": "'$USERNAME'",
                "password": "'$PASSWORD'"
            },
            "id": 1
        }' | jq -r '.result'
}

# Função para criar host
create_host() {
    local hostname=$1
    local mikrotik_ip=$2
    local token=$3
    
    curl -s -X POST $ZABBIX_URL \
        -H "Content-Type: application/json" \
        -d '{
            "jsonrpc": "2.0",
            "method": "host.create",
            "params": {
                "host": "'$hostname'",
                "name": "TriplePlay Monitor - '$hostname'",
                "groups": [{"groupid": "14"}],
                "templates": [{"templateid": "10001"}],
                "macros": [
                    {"macro": "{$COLLECTOR_URL}", "value": "http://collector.empresa.com:5000"},
                    {"macro": "{$MIKROTIK_HOST}", "value": "'$mikrotik_ip'"},
                    {"macro": "{$MIKROTIK_USER}", "value": "zabbix"},
                    {"macro": "{$MIKROTIK_PASSWORD}", "value": "senha123"},
                    {"macro": "{$TARGET_DNS1}", "value": "8.8.8.8"},
                    {"macro": "{$TARGET_DNS2}", "value": "1.1.1.1"},
                    {"macro": "{$TARGET_WEB}", "value": "www.empresa.com"}
                ]
            },
            "auth": "'$token'",
            "id": 2
        }'
}

# Executar criação
TOKEN=$(get_token)
for site in "${!SITES[@]}"; do
    echo "Criando host: $site"
    create_host "$site" "${SITES[$site]}" "$TOKEN"
done
```

### Script de Atualização de Macros

```bash
#!/bin/bash
# update-macros.sh

# Atualizar senha do MikroTik em todos os hosts
update_mikrotik_password() {
    local new_password=$1
    local token=$(get_token)
    
    # Buscar hosts do template TriplePlay
    host_ids=$(curl -s -X POST $ZABBIX_URL \
        -H "Content-Type: application/json" \
        -d '{
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": ["hostid"],
                "templateids": ["10001"]
            },
            "auth": "'$token'",
            "id": 3
        }' | jq -r '.result[].hostid')
    
    # Atualizar macro em cada host
    for hostid in $host_ids; do
        curl -s -X POST $ZABBIX_URL \
            -H "Content-Type: application/json" \
            -d '{
                "jsonrpc": "2.0",
                "method": "usermacro.update",
                "params": {
                    "hostid": "'$hostid'",
                    "macro": "{$MIKROTIK_PASSWORD}",
                    "value": "'$new_password'"
                },
                "auth": "'$token'",
                "id": 4
            }'
        echo "Password updated for host $hostid"
    done
}
```

## 📊 Configuração de Tags

### Tags Recomendadas

```yaml
# Tags no nível do host para melhor organização
Tags:
  - name: "site"
    value: "matriz"
  - name: "city"  
    value: "sao-paulo"
  - name: "region"
    value: "sudeste"
  - name: "link_type"
    value: "fibra"
  - name: "criticality"
    value: "high"
```

### Uso das Tags

1. **Filtros em Dashboards**
2. **Actions baseadas em tags**
3. **Relatórios por região/tipo**
4. **Escalation baseada em criticidade**

## 🎯 Melhores Práticas

### Nomenclatura de Hosts

```yaml
# Bom
tripleplay-matriz-sp
tripleplay-filial-rj-001
tripleplay-dc-aws-us-east

# Evitar
site1
servidor-mikrotik
teste
```

### Organização de Groups

```yaml
Host Groups:
├── TriplePlay-Sentinel          # Group principal
│   ├── TriplePlay-Matriz       # Sub-group por tipo
│   ├── TriplePlay-Filiais      # Sub-group por tipo
│   └── TriplePlay-Datacenter   # Sub-group por tipo
```

### Segurança de Credenciais

1. **Use usuário específico no MikroTik**
   ```bash
   # No MikroTik
   /user add name=zabbix group=read password=senha_forte_123
   /user set zabbix group=read
   ```

2. **Configure macros no nível do host**
   - Não use macros globais para senhas
   - Uma senha comprometida não afeta todos os sites

3. **Rotação de senhas**
   - Use script de atualização automática
   - Configure alertas para senhas próximas do vencimento

## 🔍 Troubleshooting de Hosts

### Host não coleta dados

#### Verificação 1: Conectividade Collector

```bash
# Do Zabbix Server
curl -I http://collector.empresa.com:5000/api/health
```

#### Verificação 2: Conectividade MikroTik

```bash
# Do Collector
ssh zabbix@192.168.1.1 "/ip address print"
```

#### Verificação 3: Macros do Host

```sql
-- No banco Zabbix
SELECT h.host, hm.macro, hm.value 
FROM hosts h 
JOIN hostmacro hm ON h.hostid = hm.hostid 
WHERE h.host LIKE 'tripleplay%';
```

### Items em estado "Not supported"

1. **Verificar logs do Zabbix**
   ```bash
   tail -f /var/log/zabbix/zabbix_server.log | grep "tripleplay"
   ```

2. **Teste manual da API**
   ```bash
   curl -X POST http://collector:5000/api/test \
     -H "Content-Type: application/json" \
     -d '{
       "mikrotik_host": "192.168.1.1",
       "mikrotik_user": "zabbix",
       "mikrotik_password": "senha",
       "test_type": "ping", 
       "target": "8.8.8.8"
     }'
   ```

3. **Verificar timeout**
   - Aumente `{$COLLECTOR_TIMEOUT}` se necessário
   - Testes de traceroute podem demorar mais

## 📈 Monitoramento de Performance

### Métricas de Host

```sql
-- Hosts com mais items não suportados
SELECT h.host, COUNT(*) as unsupported_items
FROM hosts h
JOIN items i ON h.hostid = i.hostid  
WHERE i.state = 1 AND h.host LIKE 'tripleplay%'
GROUP BY h.host
ORDER BY unsupported_items DESC;

-- Hosts com triggers em estado desconhecido
SELECT h.host, COUNT(*) as unknown_triggers
FROM hosts h
JOIN items i ON h.hostid = i.hostid
JOIN functions f ON i.itemid = f.itemid
JOIN triggers t ON f.triggerid = t.triggerid
WHERE t.value = 2 AND h.host LIKE 'tripleplay%'
GROUP BY h.host;
```

## ✅ Checklist de Configuração

Para cada novo host:

- [ ] Host criado com nomenclatura padrão
- [ ] Template TriplePlay-Sentinel aplicado
- [ ] Todas as macros obrigatórias configuradas
- [ ] Credenciais MikroTik testadas manualmente
- [ ] Collector acessível do Zabbix Server
- [ ] Tags apropriadas configuradas
- [ ] Items coletando dados (sem "No data")
- [ ] Triggers funcionando (sem "Unknown")
- [ ] Thresholds ajustados para o tipo de link
- [ ] Host adicionado ao dashboard apropriado

---

**Próximo:** [Dashboard Setup](dashboard-setup.md)