# Configuração de Dashboards - TriplePlay-Sentinel

## 📋 Visão Geral

O template TriplePlay-Sentinel inclui dois dashboards prontos para uso, mas este guia mostra como personalizar e criar dashboards adicionais para diferentes necessidades operacionais.

## 🎨 Dashboards Inclusos

### 1. TriplePlay-Sentinel Network Monitoring
- **Público-alvo:** NOC, operadores de rede
- **Foco:** Visão geral da saúde da rede
- **Atualização:** 60 segundos

### 2. TriplePlay-Sentinel Technical Dashboard  
- **Público-alvo:** Técnicos, engenheiros
- **Foco:** Métricas detalhadas e troubleshooting
- **Atualização:** 30 segundos

## 🔧 Personalização de Dashboards

### Modificando Dashboard Existente

1. **Acessar Dashboard**
   ```
   Monitoring → Dashboards → [Nome do Dashboard]
   ```

2. **Entrar no Modo Edição**
   - Clique no ícone de configuração (⚙️)
   - Selecione **"Edit dashboard"**

3. **Modificar Widgets**
   - Clique no widget desejado
   - Ajuste configurações conforme necessário
   - **Save changes**

### Exemplo: Adicionar Novo Widget de Métricas

```yaml
Widget Type: Item
Name: "Network Quality Metrics"
Size: 6x4
Position: x=6, y=8

Items:
- tripleplay.network.quality_score
- tripleplay.ping.success_rate[{$MIKROTIK_HOST},{$TARGET_DNS1}]
- tripleplay.collector.cache_hit_rate

Display options:
- Show header: Yes
- Show timestamp: Yes  
- Columns: 3
```

## 🏢 Dashboards por Perfil de Usuário

### Dashboard Executivo

Ideal para diretores e gerentes que precisam de visão macro.

```yaml
Dashboard Name: "TriplePlay Executive Summary"
Update interval: 300s (5 min)
Auto-start: Yes

Widgets:
1. Network Health Status (Plain Text)
   - Overall network score
   - Number of sites online/offline
   - Critical alerts count

2. SLA Compliance (Gauge)
   - Network availability %
   - Performance SLA %
   - Current month compliance

3. Sites Status Map (Problems)
   - All sites status
   - Color-coded by health
   - Problem count per site

4. Trend Analysis (Graph)
   - 30-day availability trend
   - Performance trend
   - Incident count trend
```

#### Configuração do Dashboard Executivo

```yaml
# Widget 1: Network Health Summary
Type: PLAIN_TEXT
Content: |
  🌐 REDE CORPORATIVA - STATUS GERAL
  
  ✅ Sites Online: {ITEM.VALUE:tripleplay.sites.online.count}
  ❌ Sites com Problemas: {ITEM.VALUE:tripleplay.sites.problems.count}  
  📊 SLA Disponibilidade: {ITEM.VALUE:tripleplay.sla.availability}%
  ⚡ Score Qualidade Médio: {ITEM.VALUE:tripleplay.network.quality.average}

# Widget 2: SLA Gauge
Type: GAUGE
Item: tripleplay.sla.availability.current_month
Min: 0
Max: 100
Thresholds:
  - 0-95: Red
  - 95-98: Yellow  
  - 98-100: Green

# Widget 3: Critical Problems
Type: PROBLEMS
Show: Active problems only
Severity: High, Disaster
Tags: component:network
Sort: Severity (desc)
```

### Dashboard NOC (Network Operations Center)

Para operadores que monitoram 24/7.

```yaml
Dashboard Name: "TriplePlay NOC Operations"
Update interval: 30s
Auto-start: Yes
Full screen: Yes

Layout:
├── Top Row (Status Overview)
│   ├── Live Problems (4x6)
│   ├── Network Map (4x6) 
│   └── Performance Summary (4x6)
├── Middle Row (Real-time Metrics)  
│   ├── Latency Graphs (6x8)
│   └── Packet Loss Graphs (6x8)
└── Bottom Row (Detailed Analysis)
    ├── TCP Services (4x6)
    ├── Cache Performance (4x6)
    └── MikroTik Status (4x6)
```

#### Widgets do Dashboard NOC

```yaml
# Widget: Live Network Problems
Type: PROBLEMS
Size: 12x4
Filters:
  - Host groups: TriplePlay-Sentinel
  - Severity: Warning, Average, High, Disaster
  - Show: Unresolved problems
  - Sort: Last change (desc)
Options:
  - Show timeline: Yes
  - Show tags: Yes
  - Problem display: All

# Widget: Real-time Latency
Type: GRAPH  
Size: 6x6
Graph: Custom multi-host latency
Items:
  - tripleplay.ping.rtt_avg[*,8.8.8.8] (all hosts)
  - tripleplay.ping.rtt_avg[*,1.1.1.1] (all hosts)
Time period: Last 4 hours
Refresh: 30s

# Widget: Packet Loss Heatmap
Type: GRAPH
Size: 6x6  
Graph: Custom packet loss
Items:
  - tripleplay.ping.loss[*,8.8.8.8] (all hosts)
Display: Line graph with thresholds
Thresholds:
  - 0-5%: Green
  - 5-15%: Yellow
  - 15%+: Red
```

### Dashboard Técnico Avançado

Para troubleshooting detalhado.

```yaml
Dashboard Name: "TriplePlay Advanced Diagnostics" 
Update interval: 15s
Pages: 3

Page 1: Network Diagnostics
- Detailed ping statistics
- Jitter analysis  
- Traceroute metrics
- Quality scores

Page 2: Service Analysis
- TCP connection times
- Port connectivity matrix
- Service availability trends
- Response time distributions

Page 3: Infrastructure Health
- Collector performance
- Cache efficiency
- MikroTik device status
- SSH connection health
```

## 🎯 Dashboards Específicos por Cenário

### Dashboard para ISP/Provedor

```yaml
# Foco em SLA e qualidade de serviço
Widgets essenciais:
1. Customer SLA Dashboard
   - Availability per customer
   - Latency SLA compliance  
   - Packet loss SLA compliance
   - Jitter measurements

2. Network Performance Matrix
   - Per-site performance grid
   - Color-coded status
   - Trend indicators
   - Threshold violations

3. Incident Tracking
   - Active incidents
   - Resolution times
   - Impact analysis
   - Customer notifications
```

### Dashboard para Empresa Corporativa

```yaml
# Foco em conectividade de filiais
Widgets essenciais:
1. Branch Office Status
   - HQ connectivity
   - Inter-branch connectivity  
   - Internet connectivity
   - Critical applications status

2. Business Impact Analysis
   - Applications affected
   - Users impacted
   - Business processes at risk
   - Recovery time estimates

3. Cost Analysis
   - Link utilization
   - SLA penalties
   - Performance vs cost
   - Optimization opportunities
```

## 📊 Widgets Customizados

### Widget de Mapa de Rede

```yaml
Type: GEOMAP
Name: "Network Sites Geographic View"
Data source: Host inventory
Configuration:
  - Default view: World
  - Zoom: Auto-fit to data
  - Markers: Problem severity colors
  - Popup: Host details + latest problems

Host inventory required fields:
- Location: Latitude,Longitude
- Site name: Inventory name
- Address: Full address
```

### Widget de SLA em Tempo Real

```yaml
Type: GAUGE
Name: "Real-time SLA Compliance"
Formula: |
  # SLA = (Total time - Downtime) / Total time * 100
  (now() - last(/host/tripleplay.sla.downtime.total)) / now() * 100

Thresholds:
  0-99.5%: Critical (Red)
  99.5-99.9%: Warning (Yellow)  
  99.9-100%: Good (Green)

Update: 60s
```

### Widget de Trending Analysis

```yaml
Type: GRAPH
Name: "7-Day Performance Trend"
Items:
  - avg_by_hour(tripleplay.ping.rtt_avg[*,*])
  - avg_by_hour(tripleplay.ping.loss[*,*]) 
  - avg_by_hour(tripleplay.tcp.time[*,*])

Time period: 7 days
Display:
  - Show trend lines
  - Show working time
  - Show problems periods
  - Y-axis: Split (latency left, loss% right)
```

## 🔄 Automação de Dashboards

### Script para Criar Dashboard Multi-Site

```bash
#!/bin/bash
# create-multisite-dashboard.sh

create_multisite_dashboard() {
    local sites=("$@")
    local dashboard_json='
    {
        "jsonrpc": "2.0",
        "method": "dashboard.create",
        "params": {
            "name": "TriplePlay Multi-Site Overview",
            "display_period": 60,
            "auto_start": 1,
            "pages": [{
                "name": "Network Status",
                "widgets": []
            }]
        },
        "auth": "'$TOKEN'",
        "id": 1
    }'
    
    # Adicionar widget para cada site
    local widget_y=0
    for site in "${sites[@]}"; do
        local widget='{
            "type": "graph",
            "name": "Performance - '$site'",
            "x": 0,
            "y": '$widget_y',
            "width": 12,
            "height": 4,
            "fields": {
                "graph_item": {
                    "host": "'$site'",
                    "key": "tripleplay.ping.rtt_avg"
                }
            }
        }'
        
        # Adicionar widget ao dashboard JSON
        widget_y=$((widget_y + 4))
    done
    
    # Executar criação
    curl -X POST $ZABBIX_URL -d "$dashboard_json"
}

# Uso
SITES=("tripleplay-matriz" "tripleplay-filial-sp" "tripleplay-filial-rj")
create_multisite_dashboard "${SITES[@]}"
```

### Template de Dashboard para Novos Sites

```json
{
  "dashboard_template": {
    "name": "TriplePlay Site - {SITE_NAME}",
    "widgets": [
      {
        "type": "plaintext",
        "content": "📍 Site: {SITE_NAME}\n🌐 MikroTik: {MIKROTIK_IP}\n📊 Status: {STATUS}"
      },
      {
        "type": "graph", 
        "graph": "Network Performance - {SITE_NAME}",
        "time_period": 3600
      },
      {
        "type": "problems",
        "host_filter": "{SITE_HOST}",
        "severity_filter": ">=Average"
      }
    ]
  }
}
```

## 📱 Dashboards Responsivos

### Configuração para Mobile

```yaml
Mobile-friendly settings:
- Widget minimum width: 12 (full width)
- Reduce number of widgets per page
- Larger fonts and charts
- Simplified layouts
- Touch-friendly controls

Example mobile dashboard:
1. Status Summary (text only)
2. Critical Problems (list view)  
3. Key Metrics (large numbers)
4. Quick Actions (buttons)
```

### Dashboard para TV/Monitor de Parede

```yaml
TV Dashboard settings:
- Auto-refresh: 30s
- Full screen mode: Always
- High contrast colors
- Large fonts (minimum 16px)
- No interactive elements
- Auto-rotate pages: 60s per page

Layout for 1920x1080:
├── Header: Company logo + timestamp
├── Main area: 4x3 widget grid
└── Footer: Alert ticker
```

## 🎨 Temas e Personalização Visual

### Cores por Severidade

```yaml
Problem severity colors:
- Disaster: #FF0000 (Red)
- High: #FF8000 (Orange)  
- Average: #FFFF00 (Yellow)
- Warning: #00FFFF (Cyan)
- Information: #00FF00 (Green)

Performance colors:
- Excellent (>95%): #00AA00
- Good (90-95%): #AAAA00  
- Fair (80-90%): #AA5500
- Poor (<80%): #AA0000
```

### Corporate Branding

```yaml
# Custom CSS for corporate look
.dashboard-header {
    background: linear-gradient(to right, #1e3c72, #2a5298);
    color: white;
    font-family: 'Corporate Font', sans-serif;
}

.widget-tripleplay {
    border-left: 4px solid #2a5298;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.status-excellent { background-color: #d4edda; }
.status-good { background-color: #fff3cd; }
.status-fair { background-color: #f8d7da; }
.status-poor { background-color: #f5c6cb; }
```

## 📈 Métricas de Performance do Dashboard

### Monitoramento de Uso

```sql
-- Dashboard mais acessado
SELECT d.name, COUNT(*) as access_count
FROM dashboard_access_log dal
JOIN dashboards d ON dal.dashboard_id = d.dashboardid  
WHERE dal.access_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
AND d.name LIKE '%TriplePlay%'
GROUP BY d.name
ORDER BY access_count DESC;

-- Widgets com maior tempo de carregamento
SELECT w.name, AVG(w.load_time_ms) as avg_load_time
FROM widget_performance_log w
WHERE w.dashboard_name LIKE '%TriplePlay%'
GROUP BY w.name
ORDER BY avg_load_time DESC;
```

### Otimização de Performance

```yaml
Best practices:
1. Limit widgets per page: Maximum 12
2. Use appropriate time ranges: Avoid excessive history
3. Optimize queries: Use proper item intervals
4. Cache static content: Company logos, static text
5. Minimize auto-refresh: Only when necessary

Performance targets:
- Dashboard load time: <3 seconds
- Widget refresh time: <1 second  
- API response time: <500ms
- Memory usage: <100MB per session
```

## ✅ Checklist de Dashboard

Para cada novo dashboard:

- [ ] Nome descritivo e padronizado
- [ ] Público-alvo definido
- [ ] Período de atualização apropriado
- [ ] Widgets essenciais incluídos
- [ ] Cores e temas consistentes
- [ ] Responsivo para diferentes telas
- [ ] Testado com dados reais
- [ ] Documentação de uso criada
- [ ] Permissões de acesso configuradas
- [ ] Backup da configuração realizado

## 🔧 Troubleshooting de Dashboards

### Problemas Comuns

1. **Widgets não carregam**
   - Verificar permissões do usuário
   - Validar consultas de dados
   - Confirmar conectividade com hosts

2. **Performance lenta**
   - Reduzir período de tempo
   - Otimizar número de widgets
   - Verificar carga do servidor

3. **Dados não atualizando**
   - Confirmar coleta de items
   - Verificar intervalos de refresh
   - Validar status dos hosts

---

**Documentação relacionada:**
- [Import Guide](import-guide.md)
- [Host Configuration](host-configuration.md)
- [Zabbix API Documentation](https://www.zabbix.com/documentation/6.0/manual/api)