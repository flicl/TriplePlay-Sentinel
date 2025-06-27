# Configuração do Zabbix para o Sentinel

Este guia detalha como configurar o Zabbix para integração com o sistema Sentinel utilizando **arquitetura HTTP Agent (PULL)```json
{
  "mikrotik_ip": "{$MIKROTIK_IP}",      # Dispositivo controlado pelo Zabbix
  "mikrotik_user": "{$MIKROTIK_USER}",
  "mikrotik_pass": "{$MIKROTIK_PASSWORD}",
  "mikrotik_port": "{$MIKROTIK_PORT}",
  "target_ip": "{$TARGET_IP}",          # Alvo definido pelo Zabbix
  "test_type": "tcp",                   # Tipo controlado centralmente
  "tcp_port": "{$TCP_PORT}"             # Porta definida por macro
}
```

## Pré-processamento JSONPath - Extração Automática

O Zabbix processa automaticamente as respostas JSON do collector usando JSONPath, extraindo métricas específicas sem necessidade de scripts externos:

### 🔍 Extração Inteligente de Métricas:
- **Ping Latency (Average)**: `$.average_latency_ms` - Latência média extraída automaticamente
- **Ping Packet Loss (%)**: `$.packet_loss_percent` - Percentual de perda calculado
- **TCP Connection Time**: `$.connection_time_ms` - Tempo de conexão medido
- **TCP Connection Status**: `$.status` → (convertido para 1 se "success", 0 se "failed")

### 🚀 Vantagens do Pré-processamento:
- **Processamento Local**: Extração realizada no próprio Zabbix
- **Sem Dependências**: Não requer scripts externos ou agentes
- **Performance**: Processamento otimizado e rápido
- **Confiabilidade**: Menos pontos de falha no sistemantém controle total sobre o monitoramento, incluindo a importação do template, configuração de hosts e definição de macros.

## 🎯 Vantagens da Arquitetura HTTP Agent (PULL)

### Controle Total pelo Zabbix:
- **QUANDO**: Zabbix determina frequência e timing dos testes
- **ONDE**: Zabbix escolhe quais dispositivos monitorar  
- **O QUE**: Zabbix define tipos de teste e parâmetros
- **COMO**: Zabbix processa resultados com JSONPath automático

### Eficiência Superior:
- **Cache Inteligente**: TTL de 30 segundos evita testes redundantes
- **Sem Sobrecarga**: Dispositivos MikroTik não executam scripts locais
- **Recursos Otimizados**: Processamento centralizado no collector
- **Escalabilidade**: Múltiplos collectors gerenciados centralmente

## Pré-requisitos

- Zabbix Server 5.0 ou superior
- Acesso administrativo ao frontend do Zabbix
- Collector do Sentinel instalado e operacional
- Dispositivos MikroTik com API ou SSH habilitados

## Importação do Template Sentinel

1. Faça o download do arquivo de template (`sentinel_template.xml`) disponível no diretório `templates` do projeto.

2. Acesse o frontend do Zabbix e navegue até **Configuration** > **Templates**.

3. Clique no botão **Import** no canto superior direito.

4. Na tela de importação:
   - Clique em **Choose File** e selecione o arquivo `sentinel_template.xml`.
   - Mantenha as opções padrão de importação.
   - Clique em **Import**.

5. Confirme que o template "Sentinel - Network Monitoring" aparece na lista de templates.

## Configuração de Hosts

### Criando um Novo Host

1. Navegue até **Configuration** > **Hosts**.

2. Clique em **Create host** no canto superior direito.

3. Na seção **Host**:
   - Digite um nome para o host (geralmente o nome do dispositivo MikroTik).
   - Defina o **Groups** apropriado (ex: "MikroTik Routers").
   - Em **Interfaces**, adicione a interface do dispositivo MikroTik (IP e porta).

4. Na seção **Templates**, clique em **Select** e adicione o template "Sentinel - Network Monitoring".

5. Na seção **Macros**, configure as macros necessárias (detalhadas abaixo).

6. Clique em **Add** para criar o host.

### Macros do Host

Configure as seguintes macros para cada host:

| Macro | Descrição | Exemplo |
|-------|-----------|---------|
| `{$MIKROTIK_IP}` | Endereço IP do dispositivo MikroTik | `192.168.1.1` |
| `{$MIKROTIK_USER}` | Nome de usuário para acesso ao MikroTik | `admin` |
| `{$MIKROTIK_PASSWORD}` | Senha para acesso ao MikroTik | `senha123` |
| `{$MIKROTIK_PORT}` | Porta API do MikroTik (padrão: 8728 para API, 22 para SSH) | `8728` |
| `{$TARGET_IP}` | Endereço IP alvo para os testes | `8.8.8.8` |
| `{$TEST_TYPE}` | Tipo de teste a ser executado ("ping" ou "tcp") | `ping` |

## Usando o IP do Host como Alvo de Monitoramento

Para monitorar o próprio host como alvo (em vez de um IP fixo), você pode usar a macro embutida do Zabbix `{HOST.IP}` da seguinte forma:

1. Nas configurações de macros do host, defina a macro `{$TARGET_IP}` com o valor `{HOST.IP}`:
   - Navegue até **Configuration** > **Hosts**
   - Selecione o host desejado
   - Vá para a aba **Macros**
   - Adicione ou edite a macro `{$TARGET_IP}` com o valor `{HOST.IP}`

2. Isso fará com que o sistema Sentinel utilize o IP do próprio host como alvo para os testes de ping e TCP.

> **Nota**: As macros embutidas do Zabbix como `{HOST.IP}` só funcionam quando definidas no nível do host, não como valor padrão no template.

| `{$PING_COUNT}` | Número de pacotes ping a serem enviados | `10` |
| `{$PING_TIMEOUT}` | Timeout de cada pacote ping em segundos | `1` |
| `{$TCP_PORT}` | Porta TCP para o teste de conexão | `80` |
| `{$HIGH_LATENCY_THRESHOLD}` | Limite para alerta de latência alta (ms) | `100` |
| `{$HIGH_LOSS_THRESHOLD}` | Limite para alerta de perda de pacotes (%) | `5` |
| `{$HIGH_JITTER_THRESHOLD}` | Limite para alerta de jitter alto (ms) | `20` |
| `{$HIGH_TCP_TIME_THRESHOLD}` | Limite para alerta de tempo de conexão TCP alto (ms) | `500` |
| `{$COLLECTOR_URL}` | URL do serviço collector | `http://collector:8000/run_test` |
| `{$AUTH_TOKEN}` | Token de autenticação para o collector | `seu_token_secreto` |

> **Nota de Segurança**: Armazenar senhas em macros do Zabbix não é o método mais seguro. Em ambientes de produção, considere utilizar o Zabbix Vault ou outro método seguro para gerenciar credenciais.

## Estrutura do Template

O template "Sentinel - Network Monitoring" inclui:

### Itens Mestres

- **Sentinel - Run Ping Test**: Item HTTP Agent que executa o teste de ping.
- **Sentinel - Run TCP Test**: Item HTTP Agent que executa o teste de conexão TCP.

### Itens Dependentes para Ping

- **Sentinel - Ping Latency (Average)**: Latência média em milissegundos.
- **Sentinel - Ping Latency (Minimum)**: Latência mínima em milissegundos.
- **Sentinel - Ping Latency (Maximum)**: Latência máxima em milissegundos.
- **Sentinel - Ping Packet Loss (%)**: Percentual de perda de pacotes.
- **Sentinel - Ping Jitter**: Variação da latência em milissegundos.
- **Sentinel - Ping Sent**: Número de pacotes enviados.
- **Sentinel - Ping Received**: Número de pacotes recebidos.
- **Sentinel - Ping Status**: Status da execução do teste.

### Itens Dependentes para TCP

- **Sentinel - TCP Connection Time**: Tempo de conexão em milissegundos.
- **Sentinel - TCP Connection Status**: Status da conexão (sucesso/falha).
- **Sentinel - TCP Connection Error**: Mensagem de erro, se houver.

### Triggers

- **High Ping Latency**: Alerta quando a latência média excede o threshold.
- **High Packet Loss**: Alerta quando a perda de pacotes excede o threshold.
- **High Jitter**: Alerta quando o jitter excede o threshold.
- **TCP Connection Failed**: Alerta quando a conexão TCP falha.
- **High TCP Connection Time**: Alerta quando o tempo de conexão TCP excede o threshold.
- **No Data from Collector**: Alerta quando não há dados recebidos do collector.

## Detalhes da Configuração HTTP Agent - Arquitetura PULL

Os itens HTTP Agent são o coração da arquitetura PULL, permitindo que o Zabbix mantenha controle total sobre o monitoramento. A configuração típica demonstra como o Zabbix orquestra cada aspecto:

### 🎯 Controle de Requisições
O Zabbix envia requisições estruturadas em intervalos controlados, utilizando macros que são expandidas automaticamente:

### URL do Collector
```
{$COLLECTOR_URL}  # Exemplo: http://sentinel-collector:8000/api/test
```

### Headers de Autenticação
```
Content-Type: application/json
Authorization: Bearer {$AUTH_TOKEN}
```

### 📊 Payload JSON Controlado - Teste de Ping
```json
{
  "mikrotik_ip": "{$MIKROTIK_IP}",      # Zabbix define qual dispositivo
  "mikrotik_user": "{$MIKROTIK_USER}",   # Credenciais gerenciadas pelo Zabbix
  "mikrotik_pass": "{$MIKROTIK_PASSWORD}",
  "mikrotik_port": "{$MIKROTIK_PORT}",
  "target_ip": "{$TARGET_IP}",           # Zabbix define o alvo
  "test_type": "ping",                   # Zabbix controla tipo de teste
  "ping_count": "{$PING_COUNT}",         # Parâmetros controlados
  "ping_timeout": "{$PING_TIMEOUT}"
}
```

### 📊 Payload JSON Controlado - Teste TCP
```json
{
  "mikrotik_ip": "{$MIKROTIK_IP}",
  "mikrotik_user": "{$MIKROTIK_USER}",
  "mikrotik_pass": "{$MIKROTIK_PASSWORD}",
  "mikrotik_port": "{$MIKROTIK_PORT}",
  "target_ip": "{$TARGET_IP}",
  "test_type": "tcp",
  "tcp_port": "{$TCP_PORT}"
}
```

## Pré-processamento

Os itens dependentes utilizam pré-processamento JSONPath para extrair valores específicos da resposta JSON:

- **Ping Latency (Average)**: `$.average_latency_ms`
- **Ping Packet Loss (%)**: `$.packet_loss_percent`
- **TCP Connection Time**: `$.connection_time_ms`
- **TCP Connection Status**: `$.status` (convertido para 1 se "success", 0 se "failed")

## Dashboards

O template inclui dashboards pré-configurados:

1. **Sentinel - Visão Geral**: Visão consolidada de todos os dispositivos monitorados.
2. **Sentinel - Detalhes do Dispositivo**: Detalhes específicos para um único dispositivo.
3. **Sentinel - Análise por Destino**: Agrupamento de métricas por IP alvo.

## Configuração Avançada

### Monitoramento de Múltiplos Alvos

Para monitorar múltiplos alvos a partir do mesmo MikroTik:

1. Duplique os itens HTTP Agent no template.
2. Defina macros adicionais para cada alvo (ex: `{$TARGET_IP_1}`, `{$TARGET_IP_2}`).
3. Atualize o corpo das requisições para usar as macros específicas.

### Discovery de Alvos (LLD)

Para implementar descoberta automática de alvos:

1. Crie um script de descoberta que retorne os alvos a serem monitorados.
2. Configure uma regra LLD no template do Zabbix.
3. Defina protótipos de itens, triggers e gráficos.

## ⚙️ Configuração Avançada do HTTP Agent

### Otimizações para Arquitetura PULL

#### Configuração de Intervalos Inteligentes:
```
Item HTTP Agent - Configuração Recomendada:
- Tipo: HTTP Agent
- Intervalo: 1m (60s) - maior que TTL do cache (30s)
- Timeout: 30s - permite tempo suficiente para execução
- Retry: 3 tentativas automáticas pelo Zabbix
- Keep alive: Sim - reutiliza conexões TCP
```

#### Headers Essenciais para Performance:
```
Content-Type: application/json
Authorization: Bearer {$AUTH_TOKEN}
Connection: keep-alive
User-Agent: Zabbix-Sentinel-Agent/1.0
```

#### Configuração de Timeout Escalonado:
```
Timeout do HTTP Agent: 30s
  ├── Timeout de conexão ao collector: 5s
  ├── Timeout SSH/API para MikroTik: 15s  
  └── Buffer de processamento: 10s
```

### 🎯 Estratégias de Cache e TTL

#### Cache Inteligente do Collector:
```python
# TTL configurável por tipo de teste
CACHE_CONFIG = {
    "ping": 30,      # 30 segundos para ping
    "tcp": 60,       # 60 segundos para TCP connect
    "traceroute": 300 # 5 minutos para traceroute
}
```

#### Coordenação Zabbix ↔ Cache:
- **Intervalo Zabbix > TTL Cache**: Garante dados sempre frescos quando necessário
- **Múltiplos Hosts**: Cache compartilhado otimiza recursos para alvos comuns
- **Cache Miss Strategy**: Execução imediata + cache para próximas requisições

### 📊 Monitoramento do Próprio Sistema (Meta-Monitoring)

#### Itens de Controle Interno:
```json
# Endpoint especial para health check
POST {$COLLECTOR_URL}/health
Response: {
  "status": "healthy",
  "cache_hits": 1250,
  "cache_misses": 89,
  "active_connections": 3,
  "avg_response_time_ms": 245
}
```

#### Itens HTTP Agent para Meta-Monitoring:
- **Collector Health Status**: Monitor se o collector está responden