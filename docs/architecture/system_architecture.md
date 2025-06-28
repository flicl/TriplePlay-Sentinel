# Arquitetura do Sistema Sentinel

## Visão Geral

O Sentinel é um sistema de monitoramento centralizado que integra dispositivos MikroTik com o Zabbix através de uma **arquitetura HTTP Agent (PULL)**, proporcionando monitoramento avançado de conectividade de rede com **controle total do Zabbix**. O sistema foi projetado para eliminar a necessidade de scripts locais nos dispositivos MikroTik, centralizando a execução e o processamento dos testes sob a orquestração completa do Zabbix.

### 🎯 Arquitetura PULL - Vantagens Chave
- **Controle Total pelo Zabbix**: O Zabbix decide QUANDO, ONDE, O QUE e COMO monitorar
- **Eficiência de Recursos**: Sistema inteligente com cache e controle de requisições
- **Escalabilidade**: Múltiplos collectors podem ser gerenciados centralmente
- **Simplicidade**: Sem necessidade de agentes ou scripts nos dispositivos MikroTik

## Componentes Principais

### 1. Zabbix Server/Proxy (Maestro da Orquestração)

- **Controle Total**: Define QUANDO, ONDE, O QUE e COMO monitorar
- Utiliza itens HTTP Agent para enviar requisições controladas ao collector
- Determina frequência, alvos e parâmetros de cada teste
- Processa os resultados via pré-processamento JSONPath automático
- Executa triggers baseadas nos resultados coletados
- Apresenta dashboards com os dados processados
- **Cache-aware**: Respeita TTL e estratégias de cache do collector

### 2. Collector (`collector.py`) - Executor Inteligente

- **Resposta sob Demanda**: Atende apenas requisições HTTP do Zabbix
- Recebe requisições controladas do Zabbix via HTTP(S) Agent
- Implementa cache inteligente com TTL de 30 segundos para eficiência
- Conecta aos dispositivos MikroTik via API nativa do RouterOS
- Executa comandos remotamente nos dispositivos sob controle do Zabbix
- Processa os resultados e retorna dados estruturados em JSON
- **Auto-regulação**: Evita sobrecarga através de cache e validação
- Instalado diretamente no servidor Zabbix ou em um container Docker
- Implementado em Python utilizando Flask e librouteros
- Endpoints RESTful otimizados para integração com HTTP Agent
- Processamento assíncrono de múltiplas requisições simultâneas
- Validação rigorosa de dados e tratamento inteligente de erros

### 3. Dispositivos MikroTik (RouterOS)

- Executam os testes de conectividade (ping, TCP connect, etc.)
- Comunicam-se com o collector via API nativa do RouterOS
- Não necessitam de scripts ou configurações especiais

### 4. Configuração/Credenciais

- Armazenadas em volumes Docker ou variáveis de ambiente
- Opcionalmente podem ser recebidas do Zabbix via macros

## Diagrama de Arquitetura

```mermaid
flowchart LR
   A[Zabbix\nServer/Proxy] -->|HTTP(S) Request\nItem HTTP Agent| B[collector.py\nDocker Container]
   B -->|API/SSH| C[Dispositivos\nMikroTik\nRouterOS]
   C -->|API/SSH Result| B
   B -->|HTTP(S) Response\nJSON Data| A
   B -.->|Configuração/\nCredenciais| D[(Volume/Env\nVars/DB)]
```

## Fluxo de Dados - Arquitetura PULL Controlada

### 🔄 Processo Orquestrado pelo Zabbix:

1. **Zabbix Inicia**: O Zabbix Server/Proxy inicia requisição HTTP Agent em intervalos controlados
2. **Requisição Estruturada**: Envia POST para o collector com payload JSON contendo macros expandidas
3. **Collector Responde**: Verifica cache (TTL 30s) ou executa teste conforme solicitado
4. **Conexão MikroTik**: Estabelece conexão com dispositivo via API/SSH apenas quando necessário
5. **Execução Remota**: Executa comando específico no MikroTik sob demanda do Zabbix
6. **Resultado Processado**: MikroTik retorna dados que são estruturados pelo collector
7. **JSON Estruturado**: Collector retorna resposta JSON padronizada para o Zabbix
8. **Pré-processamento**: Zabbix extrai valores via JSONPath automaticamente
9. **Propagação**: Valores são distribuídos para itens dependentes instantaneamente
10. **Triggers/Dashboards**: Sistema avalia condições e atualiza visualizações

### 🚀 Vantagens da Arquitetura PULL:
- **Controle Centralizado**: Zabbix mantém controle total sobre timing e recursos
- **Eficiência Máxima**: Cache inteligente evita requisições desnecessárias
- **Escalabilidade**: Múltiplos collectors sem conflitos de timing
- **Confiabilidade**: Retry automático e tratamento de falhas pelo Zabbix

## Escalabilidade - Arquitetura PULL Distribuída

A arquitetura HTTP Agent (PULL) do Sentinel oferece escalabilidade superior:

### 🎯 Escalabilidade Horizontal:
- **Múltiplos Collectors**: Várias instâncias podem operar independentemente
- **Load Balancing**: Zabbix pode distribuir requisições entre collectors
- **Cache Distribuído**: Cada collector gerencia seu próprio cache inteligente
- **Controle Centralizado**: Zabbix mantém orquestração de toda a infraestrutura

### 📊 Gerenciamento de Recursos:
- **TTL Inteligente**: Cache de 30 segundos evita sobrecarga de dispositivos
- **Controle de Frequência**: Zabbix determina intervalos ideais de monitoramento
- **Auto-regulação**: Sistema se adapta automaticamente à carga
- **Balanceamento Automático**: Distribuição inteligente de testes entre dispositivos

## Considerações de Segurança

- Comunicação entre Zabbix e collector via HTTPS
- Autenticação via token no header de requisição
- Credenciais para MikroTik protegidas via variáveis de ambiente ou volume Docker
- Suporte para autenticação por chave SSH nos dispositivos MikroTik

## Extensibilidade

A arquitetura modular permite fácil adição de novos tipos de testes e funcionalidades:

- Novos comandos e testes no MikroTik
- Suporte para outros dispositivos além do MikroTik
- Integração com filas de mensagens para processamento assíncrono
- Armazenamento de histórico ou estatísticas adicionais