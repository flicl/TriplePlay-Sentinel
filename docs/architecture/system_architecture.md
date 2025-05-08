# Arquitetura do Sistema Sentinel

## Visão Geral

O Sentinel é um sistema de monitoramento centralizado que integra dispositivos MikroTik com o Zabbix para proporcionar monitoramento avançado de conectividade de rede. O sistema foi projetado para eliminar a necessidade de scripts locais nos dispositivos MikroTik, centralizando a execução e o processamento dos testes.

## Componentes Principais

### 1. Zabbix Server/Proxy

- Define os parâmetros do monitoramento (o quê, quem, para onde)
- Utiliza itens HTTP Agent para enviar requisições ao collector
- Processa os resultados via pré-processamento JSON
- Executa triggers baseadas nos resultados
- Apresenta dashboards com os dados coletados

### 2. Collector (`collector.py`)

- Componente central do sistema
- Recebe requisições do Zabbix via HTTP(S)
- Conecta aos dispositivos MikroTik via API ou SSH
- Executa comandos remotamente nos dispositivos
- Processa os resultados e retorna dados estruturados
- Dockerizado para fácil implantação e escalabilidade
- Implementado em Python utilizando Flask e Paramiko
- Endpoints RESTful para integração com sistemas externos
- Processamento assíncrono de múltiplas requisições
- Validação de dados e tratamento de erros

### 3. Dispositivos MikroTik (RouterOS)

- Executam os testes de conectividade (ping, TCP connect, etc.)
- Comunicam-se com o collector via API ou SSH
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

## Fluxo de Dados

1. O Zabbix inicia uma requisição HTTP POST para o collector, incluindo parâmetros como o IP do MikroTik, credenciais, IP alvo e tipo de teste.
2. O collector recebe a requisição, autentica e processa os parâmetros.
3. O collector estabelece uma conexão com o MikroTik especificado (via API ou SSH).
4. O collector executa o comando de teste apropriado no MikroTik.
5. O MikroTik retorna o resultado do teste para o collector.
6. O collector processa o resultado, extraindo métricas relevantes (latência, perda de pacotes, etc.).
7. O collector retorna um JSON estruturado para o Zabbix.
8. O Zabbix processa o JSON, extraindo valores individuais através de pré-processamento.
9. O Zabbix atualiza os itens dependentes com os valores extraídos.
10. O Zabbix avalia triggers baseadas nos valores recebidos.
11. Gráficos e dashboards são atualizados com os novos dados.

## Escalabilidade

A arquitetura do Sentinel permite fácil escalabilidade horizontal:

- Múltiplas instâncias do collector podem ser executadas em paralelo
- Load balancers podem distribuir a carga entre os collectors
- Cada collector pode gerenciar múltiplos MikroTiks e testes
- O Zabbix pode distribuir os testes entre diferentes collectors

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