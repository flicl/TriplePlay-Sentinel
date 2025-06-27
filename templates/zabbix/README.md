# TriplePlay-Sentinel Zabbix Template 6.0

**Versão:** 2.1.0 | **Status:** ✅ Production Ready | **Última Atualização:** 23/06/2025

## 📋 Visão Geral

Este template foi desenvolvido especificamente para o Zabbix 6.0+ e oferece monitoramento completo de rede através do TriplePlay-Sentinel Collector. O template utiliza HTTP Agent items para comunicação com a API REST do collector.

**🧹 TEMPLATE LIMPO E OTIMIZADO (v2.1.0)** - Todas as referências a funcionalidades TCP não implementadas foram removidas para maior clareza, performance e confiabilidade.

## 🚀 Características Principais

### Monitoramento de Conectividade ✅
- **Ping ICMP**: Latência, jitter, perda de pacotes e disponibilidade
- **Traceroute**: Análise de rotas de rede e número de hops
- **Cache Intelligence**: Métricas de performance do cache

### Monitoramento do Collector ✅
- **Health Check**: Status do collector e tempo de uptime
- **Performance**: Taxa de acerto do cache e métricas de performance
- **MikroTik Connection**: Status da conexão SSH com dispositivos MikroTik

### Discovery Rules ✅
- **Network Targets Discovery**: Descoberta automática de alvos de rede
- **Dynamic Item Creation**: Criação automática de itens para novos alvos

### Funcionalidades Removidas ❌
- **Testes TCP**: Removidos completamente (não implementados no collector)
- **HTTP/HTTPS Monitoring**: Não suportado pela arquitetura atual
- **Port Connectivity**: Template focado apenas em ping/traceroute

### Monitoramento do Collector
- **Health Check**: Status do collector e tempo de uptime
- **Performance**: Taxa de acerto do cache e métricas de performance
- **MikroTik Connection**: Status da conexão SSH com dispositivos MikroTik

### Discovery Rules
- **Network Targets Discovery**: Descoberta automática de alvos de rede
- **Dynamic Item Creation**: Criação automática de itens para novos alvos

## 📦 Arquivos do Template

```
templates/zabbix/
├── tripleplay-sentinel-template.yml    # Template principal Zabbix 6.0
├── README.md                          # Este arquivo
└── examples/
    ├── import-guide.md               # Guia de importação
    ├── host-configuration.md         # Configuração de hosts
    └── dashboard-setup.md            # Configuração de dashboards
```

## 🔧 Instalação e Configuração

### Pré-requisitos

1. **Zabbix Server 6.0+**
2. **TriplePlay-Sentinel Collector** rodando e acessível
3. **Dispositivo MikroTik** configurado com SSH
4. **Conectividade** entre Zabbix Server e Collector

### Passo 1: Importar o Template

1. Acesse o Zabbix Frontend
2. Vá para **Configuration** → **Templates**
3. Clique em **Import**
4. Selecione o arquivo `tripleplay-sentinel-template.yml`
5. Configure as opções de importação:
   - ✅ **Groups**: Import
   - ✅ **Templates**: Import
   - ✅ **Items**: Import
   - ✅ **Triggers**: Import
   - ✅ **Graphs**: Import
   - ✅ **Dashboards**: Import
6. Clique em **Import**

### Passo 2: Criar Host

1. Vá para **Configuration** → **Hosts**
2. Clique em **Create host**
3. Configure:
   - **Host name**: `TriplePlay-Monitor-Site1` (exemplo)
   - **Visible name**: `TriplePlay Sentinel - Site 1`
   - **Groups**: Selecione `TriplePlay-Sentinel`
   - **Interfaces**: Não é necessário (usa HTTP Agent)

### Passo 3: Aplicar Template

1. Na aba **Templates** do host
2. Em **Link new templates**, digite: `TriplePlay-Sentinel Monitoring`
3. Clique em **Add**
4. Clique em **Update**

### Passo 4: Configurar Macros

Configure as macros no nível do host:

#### Macros Obrigatórias

```yaml
# Collector Configuration
{$COLLECTOR_URL} = http://192.168.1.100:5000
{$COLLECTOR_TIMEOUT} = 30s

# MikroTik Configuration  
{$MIKROTIK_HOST} = 192.168.1.1
{$MIKROTIK_USER} = admin
{$MIKROTIK_PASSWORD} = your-password

# Test Targets
{$TARGET_DNS1} = 8.8.8.8
{$TARGET_DNS2} = 1.1.1.1
{$TARGET_GATEWAY} = 192.168.1.1
```

#### Macros de Threshold (Opcionais)

```yaml
# Ping Thresholds
{$PING_LOSS_WARN} = 10
{$PING_LOSS_HIGH} = 25
{$PING_RTT_WARN} = 100
{$PING_RTT_HIGH} = 200

# Traceroute Thresholds
{$TRACEROUTE_HOPS_MAX} = 15
{$TRACEROUTE_TIME_WARN} = 5000

# Network Quality
{$NETWORK_QUALITY_MIN} = 70
{$PING_SUCCESS_RATE_MIN} = 95
```

## 📊 Dashboards Inclusos

### 1. TriplePlay-Sentinel Network Monitoring

Dashboard principal com três páginas:

- **Network Overview**: Visão geral da rede com gráficos de performance
- **Historical Analysis**: Análise histórica de 24 horas
- **Problems & Alerts**: Problemas ativos e eventos recentes

### 2. TriplePlay-Sentinel Technical Dashboard

Dashboard técnico com métricas detalhadas do collector e cache.

## 🎯 Items Monitorados

### Ping Metrics (por target)
- `tripleplay.ping.loss[{$MIKROTIK_HOST},{$TARGET}]` - Perda de pacotes (%)
- `tripleplay.ping.rtt_avg[{$MIKROTIK_HOST},{$TARGET}]` - Latência média (ms)
- `tripleplay.ping.jitter[{$MIKROTIK_HOST},{$TARGET}]` - Jitter (ms)
- `tripleplay.ping.availability[{$MIKROTIK_HOST},{$TARGET}]` - Disponibilidade (%)
- `tripleplay.ping.success_rate[{$MIKROTIK_HOST},{$TARGET}]` - Taxa de sucesso (%)

### Traceroute Metrics
- `tripleplay.traceroute.hops[{$MIKROTIK_HOST},{$TARGET}]` - Número de hops
- `tripleplay.traceroute.reached[{$MIKROTIK_HOST},{$TARGET}]` - Alcançou destino

### Collector Health
- `tripleplay.collector.health` - Status do collector
- `tripleplay.collector.uptime` - Tempo de uptime (s)
- `tripleplay.collector.cache_hit_rate` - Taxa de acerto cache (%)

### MikroTik Connection
- `tripleplay.mikrotik.connection_status` - Status conexão SSH
- `tripleplay.mikrotik.response_time` - Tempo de resposta SSH (ms)

### Network Quality
- `tripleplay.network.quality_score` - Score de qualidade da rede

## 🚨 Triggers Configurados

### Severity Levels

- **🔥 DISASTER**: Problemas críticos que impedem monitoramento
- **🔴 HIGH**: Problemas sérios que afetam disponibilidade
- **🟡 AVERAGE**: Problemas moderados de performance
- **🟠 WARNING**: Avisos preventivos

### Principais Triggers

#### Network Connectivity
- Total packet loss (DISASTER)
- High packet loss >25% (HIGH)  
- Moderate packet loss >10% (AVERAGE)
- High latency >200ms (HIGH)
- Moderate latency >100ms (AVERAGE)

#### Service Availability
- Collector unhealthy (DISASTER)
- Low cache hit rate (WARNING)

#### Collector Health
- Collector unhealthy (DISASTER)
- Low cache hit rate (WARNING)

#### MikroTik Connection
- SSH connection failed (DISASTER)
- Slow SSH response (WARNING)

## 🔍 Troubleshooting

### Problema: Items não coletam dados

**Verificações:**
1. Collector está rodando e acessível
2. URL do collector está correta na macro `{$COLLECTOR_URL}`
3. Credenciais MikroTik estão corretas
4. Firewall permite conexão Zabbix → Collector

### Problema: Triggers em estado UNKNOWN

**Possíveis causas:**
- Erro na API do collector
- Timeout de requisição
- Formato de resposta inválido

**Solução:**
1. Teste manual da API: `curl -X POST http://collector:5000/api/test`
2. Verifique logs do Zabbix Server
3. Aumente timeout se necessário

### Problema: Discovery não encontra targets

**Verificação:**
- Endpoint `/api/discovery/targets` retorna dados válidos
- Formato JSON está correto
- JSONPath na discovery rule está correto

## 📈 Customização

### Adicionando Novos Targets

1. Configure macro com novo target: `{$TARGET_CUSTOM} = 1.2.3.4`
2. Clone items existentes
3. Substitua referência de target
4. Ajuste triggers se necessário

### Modificando Thresholds

Ajuste as macros de threshold conforme suas necessidades:

```yaml
{$PING_LOSS_WARN} = 5      # Mais rigoroso
{$PING_RTT_HIGH} = 500     # Mais permissivo
```

### Criando Dashboards Customizados

1. Use os widgets de exemplo como base
2. Adicione métricas específicas do seu ambiente
3. Configure filtros por tags
4. Ajuste períodos de visualização

## 🔗 Integração com Outras Ferramentas

### Grafana Integration
- Use Zabbix como datasource
- Importe métricas via Zabbix API
- Crie dashboards customizados

### Alerting Integration
- Configure actions no Zabbix
- Integre com Slack, Teams, PagerDuty
- Use webhooks para automações

## 📚 Referências

- [Zabbix 6.0 Documentation](https://www.zabbix.com/documentation/6.0)
- [HTTP Agent Items](https://www.zabbix.com/documentation/6.0/manual/config/items/itemtypes/http)
- [Template Guidelines](https://www.zabbix.com/documentation/6.0/manual/config/templates_out_of_the_box)
- [TriplePlay-Sentinel API Documentation](../docs/api/collector_api.md)

## 🤝 Suporte

Para problemas relacionados ao template:
1. Verifique este README
2. Consulte logs do Zabbix
3. Teste API do collector manualmente
4. Reporte issues no repositório do projeto

---

**Versão:** 2.1.0 (Template Limpo - Jun 2025)  
**Compatibilidade:** Zabbix 6.0+  
**Última atualização:** 2025-06-23
**Changelog:** Removidas todas as referências a TCP/HTTP não implementadas