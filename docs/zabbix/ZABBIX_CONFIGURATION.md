# 🛡️ TriplePlay-Sentinel - Configuração do Zabbix

## 📋 Guia Completo de Configuração Zabbix

### 1. Configuração do HTTP Agent Items

#### Item de Ping ICMP

```json
{
  "name": "TriplePlay Ping to {$TARGET}",
  "type": "HTTP Agent",
  "key": "tripleplay.ping[{$MIKROTIK_HOST},{$TARGET}]",
  "url": "http://your-collector:5000/api/test",
  "request_method": "POST",
  "post_type": "JSON",
  "posts": {
    "mikrotik_host": "{$MIKROTIK_HOST}",
    "mikrotik_user": "{$MIKROTIK_USER}",
    "mikrotik_password": "{$MIKROTIK_PASSWORD}",
    "test_type": "ping",
    "target": "{$TARGET}",
    "count": 4,
    "size": 64,
    "interval": 1
  },
  "timeout": "30s",
  "headers": {
    "Content-Type": "application/json"
  },
  "preprocessing": [
    {
      "type": "JSONPath",
      "parameters": ["$.status"],
      "error_handler": "CUSTOM_VALUE",
      "error_handler_params": "error"
    }
  ]
}
```

#### Item de TCP Connect

```json
{
  "name": "TriplePlay TCP Connect to {$TARGET}:{$PORT}",
  "type": "HTTP Agent", 
  "key": "tripleplay.tcp[{$MIKROTIK_HOST},{$TARGET},{$PORT}]",
  "url": "http://your-collector:5000/api/test",
  "request_method": "POST",
  "post_type": "JSON",
  "posts": {
    "mikrotik_host": "{$MIKROTIK_HOST}",
    "mikrotik_user": "{$MIKROTIK_USER}",
    "mikrotik_password": "{$MIKROTIK_PASSWORD}",
    "test_type": "tcp",
    "target": "{$TARGET}",
    "port": "{$PORT}"
  },
  "timeout": "30s",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### 2. Preprocessing com JSONPath

#### Extração de Métricas de Ping

```javascript
// Status do teste
JSONPath: $.status

// Pacotes perdidos (%)
JSONPath: $.results.ping_stats.packet_loss_percent

// Tempo médio (ms)
JSONPath: $.results.ping_stats.avg_time_ms

// Jitter (ms)
JSONPath: $.results.ping_stats.jitter_ms

// Disponibilidade (%)
JSONPath: $.results.ping_stats.availability_percent

// Cache hit
JSONPath: $.cache_hit
```

#### Extração de Métricas TCP

```javascript
// Status da conexão
JSONPath: $.results.tcp_stats.connection_successful

// Tempo de conexão (ms)
JSONPath: $.results.tcp_stats.connection_time_ms

// Status textual
JSONPath: $.results.tcp_stats.status
```

### 3. Macros do Template

```ini
# Configurações do MikroTik
{$MIKROTIK_HOST} = 192.168.1.1
{$MIKROTIK_USER} = admin
{$MIKROTIK_PASSWORD} = password

# Alvos de teste
{$TARGET_DNS1} = 8.8.8.8
{$TARGET_DNS2} = 1.1.1.1
{$TARGET_GATEWAY} = 192.168.1.1

# Portas para teste TCP
{$PORT_HTTP} = 80
{$PORT_HTTPS} = 443
{$PORT_DNS} = 53

# Thresholds de alerta
{$PING_LOSS_WARN} = 10
{$PING_LOSS_HIGH} = 25
{$PING_RTT_WARN} = 100
{$PING_RTT_HIGH} = 200

# Configurações do Collector
{$COLLECTOR_URL} = http://collector:5000
{$COLLECTOR_TIMEOUT} = 30s
```

### 4. Triggers de Alerta

#### Ping - Perda de Pacotes

```javascript
// Trigger: Perda de pacotes alta
{HOSTNAME:tripleplay.ping.packet_loss[{$MIKROTIK_HOST},{$TARGET_DNS1}].last()}>={$PING_LOSS_HIGH}

// Trigger: Perda de pacotes moderada  
{HOSTNAME:tripleplay.ping.packet_loss[{$MIKROTIK_HOST},{$TARGET_DNS1}].last()}>={$PING_LOSS_WARN} and 
{HOSTNAME:tripleplay.ping.packet_loss[{$MIKROTIK_HOST},{$TARGET_DNS1}].last()}<{$PING_LOSS_HIGH}

// Trigger: Destino inacessível
{HOSTNAME:tripleplay.ping.packet_loss[{$MIKROTIK_HOST},{$TARGET_DNS1}].last()}=100
```

#### Ping - Latência

```javascript
// Trigger: Latência alta
{HOSTNAME:tripleplay.ping.rtt_avg[{$MIKROTIK_HOST},{$TARGET_DNS1}].last()}>={$PING_RTT_HIGH}

// Trigger: Latência moderada
{HOSTNAME:tripleplay.ping.rtt_avg[{$MIKROTIK_HOST},{$TARGET_DNS1}].last()}>={$PING_RTT_WARN} and
{HOSTNAME:tripleplay.ping.rtt_avg[{$MIKROTIK_HOST},{$TARGET_DNS1}].last()}<{$PING_RTT_HIGH}
```

#### TCP - Conectividade

```javascript
// Trigger: Serviço TCP indisponível
{HOSTNAME:tripleplay.tcp.connected[{$MIKROTIK_HOST},{$TARGET_DNS1},{$PORT_HTTP}].last()}=0

// Trigger: Tempo de conexão alto
{HOSTNAME:tripleplay.tcp.time[{$MIKROTIK_HOST},{$TARGET_DNS1},{$PORT_HTTP}].last()}>5000
```

### 5. Template XML Completo

```xml
<?xml version="1.0" encoding="UTF-8"?>
<zabbix_export>
    <version>6.0</version>
    <date>2025-06-22T10:00:00Z</date>
    <groups>
        <group>
            <uuid>uuid-here</uuid>
            <name>TriplePlay-Sentinel</name>
        </group>
    </groups>
    <templates>
        <template>
            <uuid>template-uuid-here</uuid>
            <template>TriplePlay-Sentinel Monitoring</template>
            <name>TriplePlay-Sentinel Monitoring</name>
            <description>Template para monitoramento de conectividade usando TriplePlay-Sentinel Collector</description>
            <groups>
                <group>
                    <name>TriplePlay-Sentinel</name>
                </group>
            </groups>
            <items>
                <!-- Ping Items -->
                <item>
                    <uuid>item-ping-dns1-uuid</uuid>
                    <name>Ping Loss % to DNS1</name>
                    <type>HTTP_AGENT</type>
                    <key>tripleplay.ping.loss[{$MIKROTIK_HOST},{$TARGET_DNS1}]</key>
                    <history>7d</history>
                    <trends>90d</trends>
                    <value_type>FLOAT</value_type>
                    <units>%</units>
                    <url>{$COLLECTOR_URL}/api/test</url>
                    <post_type>JSON</post_type>
                    <posts>{"mikrotik_host":"{$MIKROTIK_HOST}","mikrotik_user":"{$MIKROTIK_USER}","mikrotik_password":"{$MIKROTIK_PASSWORD}","test_type":"ping","target":"{$TARGET_DNS1}","count":4}</posts>
                    <headers>Content-Type: application/json</headers>
                    <timeout>{$COLLECTOR_TIMEOUT}</timeout>
                    <preprocessing>
                        <step>
                            <type>JSONPATH</type>
                            <parameters>
                                <parameter>$.results.ping_stats.packet_loss_percent</parameter>
                            </parameters>
                            <error_handler>CUSTOM_VALUE</error_handler>
                            <error_handler_params>100</error_handler_params>
                        </step>
                    </preprocessing>
                </item>
                
                <!-- TCP Items -->
                <item>
                    <uuid>item-tcp-http-uuid</uuid>
                    <name>TCP Connect to HTTP</name>
                    <type>HTTP_AGENT</type>
                    <key>tripleplay.tcp.connected[{$MIKROTIK_HOST},{$TARGET_DNS1},{$PORT_HTTP}]</key>
                    <history>7d</history>
                    <trends>90d</trends>
                    <value_type>UNSIGNED</value_type>
                    <url>{$COLLECTOR_URL}/api/test</url>
                    <post_type>JSON</post_type>
                    <posts>{"mikrotik_host":"{$MIKROTIK_HOST}","mikrotik_user":"{$MIKROTIK_USER}","mikrotik_password":"{$MIKROTIK_PASSWORD}","test_type":"tcp","target":"{$TARGET_DNS1}","port":{$PORT_HTTP}}</posts>
                    <headers>Content-Type: application/json</headers>
                    <timeout>{$COLLECTOR_TIMEOUT}</timeout>
                    <preprocessing>
                        <step>
                            <type>JSONPATH</type>
                            <parameters>
                                <parameter>$.results.tcp_stats.connection_successful</parameter>
                            </parameters>
                            <error_handler>CUSTOM_VALUE</error_handler>
                            <error_handler_params>0</error_handler_params>
                        </step>
                        <step>
                            <type>BOOL_TO_DECIMAL</type>
                        </step>
                    </preprocessing>
                </item>
            </items>
            
            <triggers>
                <!-- Ping Triggers -->
                <trigger>
                    <uuid>trigger-ping-loss-high-uuid</uuid>
                    <expression>{TriplePlay-Sentinel Monitoring:tripleplay.ping.loss[{$MIKROTIK_HOST},{$TARGET_DNS1}].last()}&gt;={$PING_LOSS_HIGH}</expression>
                    <name>High packet loss to {$TARGET_DNS1} (&gt;={$PING_LOSS_HIGH}%)</name>
                    <priority>HIGH</priority>
                    <description>Perda de pacotes alta detectada para {$TARGET_DNS1}</description>
                </trigger>
                
                <!-- TCP Triggers -->
                <trigger>
                    <uuid>trigger-tcp-down-uuid</uuid>
                    <expression>{TriplePlay-Sentinel Monitoring:tripleplay.tcp.connected[{$MIKROTIK_HOST},{$TARGET_DNS1},{$PORT_HTTP}].last()}=0</expression>
                    <name>TCP service down on {$TARGET_DNS1}:{$PORT_HTTP}</name>
                    <priority>HIGH</priority>
                    <description>Serviço TCP indisponível em {$TARGET_DNS1}:{$PORT_HTTP}</description>
                </trigger>
            </triggers>
            
            <macros>
                <macro>
                    <macro>{$COLLECTOR_URL}</macro>
                    <value>http://collector:5000</value>
                    <description>URL do TriplePlay-Sentinel Collector</description>
                </macro>
                <macro>
                    <macro>{$MIKROTIK_HOST}</macro>
                    <value>192.168.1.1</value>
                    <description>IP do dispositivo MikroTik</description>
                </macro>
                <macro>
                    <macro>{$TARGET_DNS1}</macro>
                    <value>8.8.8.8</value>
                    <description>Primeiro servidor DNS para teste</description>
                </macro>
            </macros>
        </template>
    </templates>
</zabbix_export>
```

### 6. Dashboards Recomendados

#### Widget de Ping - Gráfico de Linhas
```json
{
  "type": "graph",
  "name": "Latência de Ping",
  "items": [
    "tripleplay.ping.rtt_avg[{$MIKROTIK_HOST},{$TARGET_DNS1}]",
    "tripleplay.ping.rtt_avg[{$MIKROTIK_HOST},{$TARGET_DNS2}]"
  ],
  "time_period": "1h"
}
```

#### Widget de Disponibilidade - Gauge
```json
{
  "type": "gauge", 
  "name": "Disponibilidade",
  "item": "tripleplay.ping.availability[{$MIKROTIK_HOST},{$TARGET_DNS1}]",
  "min": 0,
  "max": 100,
  "thresholds": [
    {"value": 95, "color": "red"},
    {"value": 99, "color": "yellow"},
    {"value": 100, "color": "green"}
  ]
}
```

### 7. Configuração de Host

#### Aplicar Template ao Host
1. Vá para **Configuration** → **Hosts**
2. Selecione o host MikroTik
3. Aba **Templates**
4. Adicione **TriplePlay-Sentinel Monitoring**
5. Configure as macros:
   - `{$MIKROTIK_HOST}`: IP do MikroTik
   - `{$MIKROTIK_USER}`: Usuário SSH
   - `{$MIKROTIK_PASSWORD}`: Senha SSH
   - `{$COLLECTOR_URL}`: URL do collector

### 8. Monitoramento do Collector

#### Health Check do Collector
```json
{
  "name": "Collector Health",
  "type": "HTTP Agent",
  "key": "tripleplay.collector.health",
  "url": "{$COLLECTOR_URL}/api/health",
  "timeout": "10s",
  "preprocessing": [
    {
      "type": "JSONPath",
      "parameters": ["$.status"],
      "error_handler": "CUSTOM_VALUE", 
      "error_handler_params": "unhealthy"
    }
  ]
}
```

#### Métricas do Cache
```json
{
  "name": "Cache Hit Rate",
  "type": "HTTP Agent",
  "key": "tripleplay.collector.cache_hit_rate",
  "url": "{$COLLECTOR_URL}/api/stats",
  "timeout": "10s",
  "preprocessing": [
    {
      "type": "JSONPath",
      "parameters": ["$.cache.hit_rate_percent"]
    }
  ]
}
```

---

**Nota**: Substitua `your-collector:5000` pela URL real do seu collector e configure as credenciais apropriadas nos macros.