# Configuração do Zabbix para o Sentinel

Este guia detalha como configurar o Zabbix para integração com o sistema Sentinel, incluindo a importação do template, configuração de hosts e definição de macros.

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

## Detalhes da Configuração HTTP Agent

Os itens HTTP Agent são configurados para enviar requisições POST para o collector. A configuração típica inclui:

### URL
```
{$COLLECTOR_URL}
```

### Headers
```
Content-Type: application/json
Authorization: Bearer {$AUTH_TOKEN}
```

### Body para Ping Test
```json
{
  "mikrotik_ip": "{$MIKROTIK_IP}",
  "mikrotik_user": "{$MIKROTIK_USER}",
  "mikrotik_pass": "{$MIKROTIK_PASSWORD}",
  "mikrotik_port": "{$MIKROTIK_PORT}",
  "target_ip": "{$TARGET_IP}",
  "test_type": "ping",
  "ping_count": "{$PING_COUNT}",
  "ping_timeout": "{$PING_TIMEOUT}"
}
```

### Body para TCP Test
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

## Solução de Problemas

Se encontrar problemas com a configuração do Zabbix:

1. Verifique o log do Zabbix Server: `tail -f /var/log/zabbix/zabbix_server.log`
2. Verifique os valores e preenchimento correto das macros.
3. Teste manualmente o endpoint do collector usando curl:
   ```bash
   curl -X POST http://collector:8000/run_test \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer seu_token_secreto" \
     -d '{"mikrotik_ip":"192.168.1.1", "mikrotik_user":"admin", ...}'
   ```
4. Verifique o acesso do Zabbix Server/Proxy ao collector (firewall, rede).
5. Confirme que o collector consegue acessar o MikroTik.