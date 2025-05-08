# Guia de Desenvolvimento do Projeto Sentinel
# Projeto Sentinel - Sistema de Monitoramento Centralizado MikroTik-Zabbix

### 1. Visão Geral do Sistema e Arquitetura

O Sentinel operará como um **gateway de monitoramento**. O Zabbix atuará como o orquestrador, definindo *o quê* monitorar e *quem* (qual MikroTik) deve realizar o teste, bem como *para onde* (qual IP alvo). O `collector.py` será o componente central que recebe essas instruções do Zabbix, as traduz em comandos executáveis no MikroTik (via API ou SSH) e retorna o resultado processado de volta ao Zabbix.

**Arquitetura Proposta:**

```mermaid
flowchart LR
   A[Zabbix\nServer/Proxy] -->|HTTP(S) Request\nItem HTTP Agent| B[collector.py\nDocker Container]
   B -->|API/SSH| C[Dispositivos\nMikroTik\nRouterOS]
   C -->|API/SSH Result| B
   B -->|HTTP(S) Response\nJSON Data| A
   B -.->|Configuração/\nCredenciais| D[(Volume/Env\nVars/DB)]
```

Esta arquitetura centralizada no `collector.py` atende aos requisitos de não ter scripts locais no MikroTik e permite escalabilidade horizontal do `collector.py` se necessário.

### 2. Desenvolvimento do `collector.py`

O coração do sistema. Requisitos de desenvolvimento:

*   **Framework Web:** Utilizar um framework Python leve e assíncrono é ideal para lidar com múltiplas requisições concorrentes eficientemente. `FastAPI` (com Uvicorn) ou `Flask` (com Gunicorn/Gevent) são boas opções. FastAPI é geralmente preferível para APIs devido ao seu desempenho e documentação automática (Swagger UI).
*   **Endpoint Único (Recomendado):** Um endpoint como `/run_test` que recebe um corpo JSON com todos os parâmetros necessários (MikroTik IP, credenciais, tipo de teste, alvo, parâmetros do teste, etc.) via método POST. Isso é mais seguro do que passar credenciais na URL.
*   **Autenticação:** Implementar um mecanismo de autenticação simples para começar, como um token secreto no header `Authorization` ou um corpo da requisição. O `collector.py` validaria este token contra um valor configurado. Para maior segurança, considerar um sistema de chave de API por servidor Zabbix ou usar certificados mTLS se a comunicação for direta entre Zabbix e `collector.py`.
*   **Parsing de Parâmetros:** Extrair os parâmetros do corpo JSON da requisição HTTP.
*   **Seleção e Conexão MikroTik:**
    *   Receber as credenciais do MikroTik na requisição.
    *   Utilizar a biblioteca `librouteros` para conexões API ou `paramiko` para conexões SSH. Ambas precisam ser instaladas.
    *   Implementar lógica para tentar a conexão (API ou SSH) e lidar com falhas.
    *   A seleção dinâmica do dispositivo MikroTik mencionado no requisito parece estar atrelada aos parâmetros recebidos na requisição do Zabbix (ou seja, o Zabbix especifica qual MikroTik usar via macros). Balanceamento e fallback entre *múltiplos coletores* seria uma funcionalidade de escalabilidade futura, mas o balanceamento/fallback para conectar *ao MikroTik* via API/SSH primário/secundário pode ser implementado no `collector.py`.
*   **Execução dos Testes:**
    *   **Ping:**
        *   Via API: Usar o comando `/ping`. Exemplo: `/ping address=X.X.X.X count=Y timeout=Z`. Parsear a saída do comando para extrair latência (average, min, max), perda de pacotes e jitter.
        *   Via SSH: Executar o comando `ping X.X.X.X count=Y timeout=Z`. Parsear a saída do stdout.
    *   **TCP Connect:**
        *   Via API: Pode-se usar o comando `/tool fetch url=tcp://X.X.X.X:PORT` e verificar o resultado, ou `/system health print` se houver alguma métrica relevante, ou até mesmo executar um script RouterOS temporário via API que tente a conexão. A execução de um pequeno script RouterOS via API que tente `connect X.X.X.X port=Y` pode ser a abordagem mais direta para testar o tempo de conexão *do MikroTik*.
        *   Via SSH: Executar um comando `tool fetch url=tcp://X.X.X.X:PORT` ou similar e parsear a saída.
    *   Implementar funções Python que executam esses comandos remotamente e retornam os resultados brutos.
*   **Processamento e Formatação:** As funções de teste devem processar a saída bruta do MikroTik e formatar os resultados em um dicionário Python, que será serializado para JSON na resposta HTTP. A estrutura JSON deve ser clara e fácil para o Zabbix (via pré-processamento) extrair as métricas.
    *   Exemplo de JSON para Ping: `{"status": "success", "average_latency_ms": 15.2, "packet_loss_percent": 0, "jitter_ms": 1.1, "sent": 10, "received": 10}`
    *   Exemplo de JSON para TCP: `{"status": "success", "connection_time_ms": 55, "error": null}`
*   **Logs:** Usar o módulo `logging` do Python para registrar requisições, parâmetros, resultados, erros e exceções com níveis de severidade apropriados. Configurar a saída para stdout/stderr para facilitar a coleta de logs pelo Docker.
*   **Tratamento de Erros:** Capturar exceções durante a conexão com MikroTik, execução de comandos, parsing de resultados, etc., e retornar respostas HTTP apropriadas (e.g., 500 Internal Server Error) com detalhes do erro no corpo JSON.
*   **Concorrência:** Utilizar as capacidades assíncronas do framework web (FastAPI/asyncio) ou um pool de threads para lidar com múltiplas requisições simultaneamente.
*   **Cache/Pool de Conexões:** Manter um dicionário ou cache de conexões API/SSH ativas, usando uma chave baseada nas credenciais do MikroTik. Reutilizar conexões existentes para reduzir o overhead de estabelecimento de conexão, mas implementar lógica de timeout e reconexão em caso de falha.
*   **Configuração:** Utilizar variáveis de ambiente ou um arquivo de configuração (YAML/JSON) montado via volume Docker para armazenar o token de autenticação, porta do servidor, e talvez um mapeamento inicial de servidores Zabbix ou credenciais (embora a ideia seja receber credenciais na requisição).

### 3. Dockerização do `collector.py`

*   **Dockerfile:**
    *   Base image: `python:3.9-slim` ou similar.
    *   Instalar dependências: `pip install fastapi uvicorn librouteros paramiko python-jose`. (python-jose para JWT se usar OAuth, mas um token simples é suficiente para começar).
    *   Copiar código da aplicação.
    *   Expor a porta de escuta (e.g., 8000).
    *   Definir variáveis de ambiente padrão.
    *   CMD ou ENTRYPOINT para rodar o servidor Uvicorn/Gunicorn.
*   **Variáveis de Ambiente:**
    *   `COLLECTOR_PORT`: Porta para o servidor HTTP.
    *   `AUTH_TOKEN`: Token secreto para autenticação.
    *   `LOG_LEVEL`: Nível de log (INFO, DEBUG, ERROR).
*   **HTTPS/TLS:** No Dockerfile, pode-se configurar diretamente se usar um framework como FastAPI que suporta TLS via Uvicorn. Alternativamente, a abordagem mais robusta para produção é rodar o container atrás de um reverse proxy (Nginx, Traefik) que gerencie o TLS. O docker-compose pode incluir a configuração para o reverse proxy.
*   **docker-compose.yml:**
    *   Definir o serviço `collector`.
    *   Configurar `build` (apontando para o diretório do Dockerfile) ou `image` (se for usar uma imagem pré-construída).
    *   Mapear portas (e.g., ` "8000:8000"`).
    *   Definir `environment` com as variáveis de ambiente.
    *   Configurar `volumes` para logs persistentes ou arquivos de configuração.
    *   Definir uma rede customizada para o Sentinel.

### 4. Integração com Zabbix

*   **Itens HTTP Agent:**
    *   Criar um item em um template Zabbix com o tipo `HTTP Agent`.
    *   Configurar a URL para apontar para o endpoint do `collector.py` (e.g., `http://ip_do_collector:port/run_test`).
    *   Configurar o método como `POST`.
    *   Configurar Headers (e.g., `Authorization: Bearer {$AUTH_TOKEN}`).
    *   Configurar o Body da requisição no formato JSON, usando macros do host para passar os parâmetros:
        ```json
        {
          "mikrotik_ip": "{$MIKROTIK_IP}",
          "mikrotik_user": "{$MIKROTIK_USER}",
          "mikrotik_pass": "{$MIKROTIK_PASSWORD}",
          "mikrotik_port": "{$MIKROTIK_PORT}",
          "target_ip": "{$TARGET_IP}",
          "test_type": "{$TEST_TYPE}",
          "ping_count": "{$PING_COUNT}",
          "ping_timeout": "{$PING_TIMEOUT}",
          "tcp_port": "{$TCP_PORT}"
        }
        ```
        *Nota:* Armazenar senhas em macros Zabbix não é ideal. Considerar usar Zabbix Vault ou passá-las via variáveis de ambiente seguras se possível, embora receber na requisição seja prático para este caso específico.
    *   Configurar o *Request timeout* e *Update interval* do item.
*   **Pré-processamento:** Adicionar passos de pré-processamento nos itens HTTP Agent para:
    *   Validar a resposta JSON.
    *   Usar JSONPath para extrair as métricas individuais (latência, perda, status, etc.) em itens dependentes.
*   **Macros:** Definir macros no nível do template ou host para configurar os parâmetros dinamicamente:
    *   `{$MIKROTIK_IP}`, `{$MIKROTIK_USER}`, `{$MIKROTIK_PASSWORD}`, `{$MIKROTIK_PORT}`
    *   `{$TARGET_IP}`: O IP que o MikroTik vai testar.
    *   `{$TEST_TYPE}`: "ping", "tcp".
    *   `{$PING_COUNT}`, `{$PING_TIMEOUT}`
    *   `{$TCP_PORT}`
*   **Templates:** Criar um template Zabbix que contenha:
    *   Os macros necessários.
    *   Itens mestre (HTTP Agent) para cada tipo de teste.
    *   Itens dependentes para cada métrica extraída via pré-processamento (latência avg, perda, jitter, tempo TCP, status).
    *   Triggers baseadas nos itens dependentes.
    *   Gráficos.
*   **LLD (Low Level Discovery):** Embora o fluxo principal seja o Zabbix definindo o alvo, LLD poderia ser usado para:
    *   Descobrir interfaces ou rotas no MikroTik e criar itens para monitorar a conectividade *dessas* interfaces/rotas para alvos específicos. Isso exigiria um endpoint no `collector.py` que execute comandos de descoberta no MikroTik.
    *   Descobrir alvos de monitoramento a partir de uma fonte externa e criar hosts/itens no Zabbix.

### 5. Template Zabbix Avançado

Detalhando os elementos do template:

*   **Itens:**
    *   Item Mestre HTTP Agent "Sentinel - Run Ping Test" (retorna JSON).
    *   Item Mestre HTTP Agent "Sentinel - Run TCP Test" (retorna JSON).
    *   Itens Dependentes de "Sentinel - Run Ping Test":
        *   "Sentinel - Ping Latency (Average)" (numeric, float) - Pré-processamento JSONPath: `$.average_latency_ms`
        *   "Sentinel - Ping Latency (Minimum)" (numeric, float) - JSONPath: `$.min_latency_ms`
        *   "Sentinel - Ping Latency (Maximum)" (numeric, float) - JSONPath: `$.max_latency_ms`
        *   "Sentinel - Ping Packet Loss (%)" (numeric, float) - JSONPath: `$.packet_loss_percent`
        *   "Sentinel - Ping Jitter" (numeric, float) - JSONPath: `$.jitter_ms`
        *   "Sentinel - Ping Sent" (numeric, unsigned) - JSONPath: `$.sent`
        *   "Sentinel - Ping Received" (numeric, unsigned) - JSONPath: `$.received`
        *   "Sentinel - Ping Status" (text/char) - JSONPath: `$.status` (útil para verificar falhas gerais na execução do teste)
    *   Itens Dependentes de "Sentinel - Run TCP Test":
        *   "Sentinel - TCP Connection Time" (numeric, float) - JSONPath: `$.connection_time_ms`
        *   "Sentinel - TCP Connection Status" (numeric, unsigned) - JSONPath: `$.status` (e.g., 1 for success, 0 for failure, ou text)
        *   "Sentinel - TCP Connection Error" (text/char) - JSONPath: `$.error`
*   **Triggers:**
    *   Trigger para Alta Latência Média: `last("Sentinel - Ping Latency (Average)") > {$HIGH_LATENCY_THRESHOLD}`
    *   Trigger para Perda de Pacotes: `last("Sentinel - Ping Packet Loss (%)") > {$HIGH_LOSS_THRESHOLD}`
    *   Trigger para Jitter Elevado: `last("Sentinel - Ping Jitter") > {$HIGH_JITTER_THRESHOLD}`
    *   Trigger para Falha de Conexão TCP: `last("Sentinel - TCP Connection Status") = 0` (se 0 for failure) ou `last("Sentinel - TCP Connection Status").str() = "failure"`
    *   Trigger para Tempo de Conexão TCP Elevado: `last("Sentinel - TCP Connection Time") > {$HIGH_TCP_TIME_THRESHOLD}`
    *   Trigger para Ausência de Dados (No Data): `nodata(5m) = 1` nos itens mestres ou dependentes cruciais.
*   **Macros de Trigger:** Definir macros como `{$HIGH_LATENCY_THRESHOLD}`, `{$HIGH_LOSS_THRESHOLD}`, etc., para facilitar a customização dos thresholds nos hosts.
*   **Gráficos:** Criar gráficos para as métricas de latência (min/avg/max), perda de pacotes, jitter, tempo de conexão TCP ao longo do tempo.
*   **Dashboards:**
    *   Criar dashboards que agreguem os gráficos e status dos triggers.
    *   "Visão Geral da Conectividade Edge": Usar widgets que mostrem os principais indicadores (latência média, perda, status TCP) para múltiplos hosts, talvez usando mapas, Top N ou painéis de status.
    *   "Dashboard Específico do Dispositivo": Um dashboard para ser usado no contexto de um host específico, mostrando todos os gráficos e triggers relacionados àquele host/MikroTik.
    *   "Análise de Destino": Se você monitorar o mesmo IP alvo a partir de diferentes MikroTiks, um dashboard que agrupe métricas por IP alvo seria útil. Isso pode exigir alguma customização ou agregação no Zabbix.

### 6. Fluxo de Dados Proposto (Reiteração)

Confirmado, o fluxo é exatamente como descrito:

1.  Zabbix (via item HTTP Agent no template Sentinel aplicado a um host) inicia uma requisição HTTP POST para o `collector.py`. A requisição inclui um corpo JSON com macros do host (MikroTik IP, credenciais, alvo, tipo de teste, etc.).
2.  O `collector.py` recebe a requisição, autentica, parseia o JSON.
3.  Com base nos parâmetros, o `collector.py` estabelece uma conexão (API ou SSH) com o MikroTik especificado.
4.  O `collector.py` executa o comando de teste apropriado no MikroTik.
5.  O `collector.py` recebe a saída do comando do MikroTik.
6.  O `collector.py` processa a saída, formata os resultados em um dicionário Python.
7.  O `collector.py` retorna uma resposta HTTP com o corpo contendo os resultados formatados em JSON de volta para o Zabbix.
8.  O item HTTP Agent no Zabbix recebe a resposta JSON.
9.  Os passos de Pré-processamento no Zabbix extraem as métricas individuais do JSON.
10. Itens dependentes são atualizados com os valores extraídos.
11. O Zabbix avalia as Triggers baseadas nos valores dos itens dependentes.
12. Alertas são gerados se as condições das triggers forem atendidas.
13. Dashboards exibem os dados históricos e o status atual das métricas.

### 7. Considerações de Segurança e Escalabilidade

*   **HTTPS:** Implementar TLS para a comunicação entre Zabbix e `collector.py` é crucial. Usar um reverse proxy (Nginx, Traefik) no Docker Compose para gerenciar certificados (Let's Encrypt, etc.) é a prática recomendada em produção. O `collector.py` escutaria em HTTP internamente no container.
*   **Credenciais MikroTik:** Evitar hardcoding. Recebê-las via requisição Zabbix (usando macros, mesmo com ressalvas) é uma opção. Para maior segurança, o `collector.py` poderia buscar as credenciais em um serviço de segredos (HashiCorp Vault, Docker Secrets, Kubernetes Secrets) usando um ID recebido na requisição. Ou ainda, usar apenas autenticação por chave SSH, onde a chave privada estaria segura no container do `collector.py` (via volume restrito) e a chave pública configurada no MikroTik.
*   **Autenticação do Collector:** O token secreto ou chave API no header `Authorization` é um bom ponto de partida. Implementar rotação de tokens periodicamente.
*   **Timeouts e Retentativas:** Implementar timeouts para as conexões API/SSH e para a execução dos comandos no MikroTik no lado do `collector.py`. Adicionar lógica de retentativa para mitigar falhas transitórias de rede ou no MikroTik.
*   **Fallback:** Se possível, configurar no Zabbix hosts diferentes que usem *MikroTiks diferentes* para testar o *mesmo alvo*. Isso fornece redundância no monitoramento. Balanceamento/fallback no `collector.py` para escolher o *melhor* MikroTik para um teste é mais complexo e pode ser uma melhoria futura.
*   **Monitoramento do Collector:** Monitorar o próprio container `collector.py` (uso de CPU, memória, logs, número de requisições, erros) usando Zabbix agent ou via metrics endpoint (se o framework web suportar, como FastAPI/Prometheus).
*   **Escalabilidade do Collector:** Docker e Docker Compose facilitam a escalabilidade horizontal. Rodar múltiplas instâncias do container `collector.py` atrás de um load balancer (gerenciado pelo Docker Compose ou um serviço externo). O Zabbix distribuiria a carga entre as instâncias.
*   **Filas de Mensagem (Futuro):** Para cenários de altíssima carga ou onde testes demorados possam bloquear o collector, integrar uma fila de mensagens (RabbitMQ, Kafka). O Zabbix enviaria a requisição para a fila, um worker do collector processaria, e outro componente atualizaria o Zabbix via Zabbix Sender. Isso adiciona complexidade, mas desacopla requisição e execução.

### 8. Documentação Completa

A documentação é fundamental para o sucesso do projeto. A estrutura proposta abrange os pontos solicitados:

**Título: Projeto Sentinel - Sistema de Monitoramento Centralizado MikroTik-Zabbix**

**Sumário:**

1.  **Introdução**
    *   O que é o Sentinel?
    *   Objetivos e benefícios (eliminar scripts locais, centralização, flexibilidade).
    *   Funcionalidades principais.
    *   Pré-requisitos (Software: Python, Docker, Docker Compose, Zabbix 5.0+; Hardware: recursos para rodar Docker e Zabbix).
2.  **Arquitetura do Sistema**
    *   Diagrama da arquitetura (Zabbix <-> Collector <-> MikroTik).
    *   Descrição dos componentes: `collector.py`, Container Docker, Zabbix Server/Proxy, Dispositivos MikroTik.
    *   Fluxo de Dados detalhado passo a passo.
3.  **Instalação e Implantação**
    *   **Instalação do Docker e Docker Compose:** Instruções para sistemas operacionais comuns (Linux, Windows, macOS - para desenvolvimento).
    *   **Construção da Imagem Docker do Collector:**
        *   Clonar o repositório do código.
        *   Comandos para construir a imagem (`docker build`).
    *   **Implantação com Docker Compose:**
        *   Descrição do arquivo `docker-compose.yml`.
        *   Configuração de variáveis de ambiente.
        *   Configuração de volumes (logs, config, certificados TLS).
        *   Instruções para iniciar (`docker compose up -d`) e parar (`docker compose down`).
    *   **Configuração de TLS (HTTPS):**
        *   Opção 1: Configurar Uvicorn/FastAPI diretamente (instruções básicas).
        *   Opção 2: Usar um Reverse Proxy (exemplo com Nginx no docker-compose, configuração básica do Nginx).
    *   **Verificação da Instalação:** Como verificar se o container está rodando e acessível.
4.  **Configuração do Zabbix**
    *   **Importação do Template Sentinel:**
        *   Passos para importar o arquivo `.xml` do template no Zabbix Frontend.
    *   **Configuração de Hosts:**
        *   Criar ou editar um Host no Zabbix.
        *   Vincular o Template Sentinel ao Host.
        *   Configurar as Macros do Host (`{$MIKROTIK_IP}`, `{$MIKROTIK_USER}`, `{$MIKROTIK_PASSWORD}`, etc.). Explicação detalhada de cada macro.
    *   **Entendendo os Itens de Monitoramento:**
        *   Descrição dos Itens Mestre (HTTP Agent) para Ping e TCP.
        *   Descrição dos Itens Dependentes e como o pré-processamento funciona (com exemplos de JSONPath).
    *   **Configuração de Triggers:**
        *   Explicação das triggers padrão incluídas no template.
        *   Como ajustar os thresholds usando Macros de Trigger.
        *   Como criar novas triggers.
    *   **Configuração de Dashboards:**
        *   Descrição dos dashboards pré-configurados (Visão Geral, Específico do Dispositivo, Análise de Destino).
        *   Como personalizar ou criar novos painéis de dashboard.
5.  **Uso e Configuração do `collector.py`**
    *   Descrição dos Endpoints (o único `/run_test`).
    *   Detalhes dos parâmetros aceitos na requisição JSON (com exemplos).
    *   Como a autenticação funciona (validação do `AUTH_TOKEN`).
    *   Configuração via variáveis de ambiente.
    *   (Opcional) Configuração via arquivo de configuração montado por volume.
    *   Formatos de Resposta JSON esperados para Ping e TCP.
6.  **Segurança**
    *   Recomendações para comunicação segura (HTTPS).
    *   Gerenciamento seguro de credenciais MikroTik (alternativas às macros do Zabbix).
    *   Segurança do container Docker.
    *   Melhores práticas de autenticação para o collector.
    *   Uso de chaves SSH em vez de senha (instruções de configuração no MikroTik e no collector).
7.  **Solução de Problemas (Troubleshooting)**
    *   Problemas comuns na instalação/inicialização do container.
    *   Falhas de comunicação entre Zabbix e Collector (firewall, IP, porta, token).
    *   Falhas de conexão entre Collector e MikroTik (firewall, credenciais, API/SSH desabilitado).
    *   Erros de parsing de resultados (saída inesperada do MikroTik).
    *   Verificação de logs do Collector.
    *   Depuração de Itens HTTP Agent no Zabbix.
    *   Ferramentas úteis (curl para testar o collector, tcpdump, ping/ssh manuais do host do collector para o MikroTik).
8.  **Extensão e Manutenção Futura**
    *   Como adicionar novos tipos de testes (ex: traceroute, teste de banda simples).
    *   Como estender o template Zabbix.
    *   Considerações para alta disponibilidade e escalabilidade (múltiplos coletores, load balancer).
    *   Integração com filas de mensagem.
    *   Automação da implantação (CI/CD).
9.  **Apêndice**
    *   Exemplo completo de arquivo `docker-compose.yml`.
    *   Exemplo de código Python básico para o endpoint `/run_test`.
    *   Exemplo de Template Zabbix (.xml - seria gerado após a implementação).

Esta estrutura fornece um guia completo para entender, implantar, configurar, usar e dar manutenção ao projeto Sentinel.

Com base neste plano e estrutura, você pode começar com a documentação e então o desenvolvimento do `collector.py` e a criação do template Zabbix. Lembre-se de iniciar com um conjunto básico de funcionalidades (ping via API, autenticação simples, dockerização) e iterar, adicionando os demais recursos gradualmente. 