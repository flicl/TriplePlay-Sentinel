# Guia do Usuário do Sentinel

Este guia fornece informações detalhadas sobre o uso do sistema Sentinel para monitoramento de conectividade através de dispositivos MikroTik e Zabbix.

## Introdução

O Sentinel é um sistema de monitoramento centralizado que permite realizar testes de conectividade (ping, TCP) a partir de dispositivos MikroTik, coletando os resultados através de um componente central (collector) e exibindo-os no Zabbix.

## Funcionalidades Principais

O Sentinel oferece as seguintes funcionalidades:

- **Testes de Ping**: Mede latência, perda de pacotes e jitter
- **Testes de Conexão TCP**: Verifica a disponibilidade de serviços e mede o tempo de estabelecimento de conexão
- **Monitoramento Centralizado**: Todos os testes são coordenados através do Zabbix
- **Dashboards**: Visualização gráfica dos resultados
- **Alertas**: Notificações configuráveis para problemas de conectividade

## Componentes do Sistema

O sistema Sentinel é composto por três componentes principais:

1. **Zabbix**: Interface de usuário e orquestrador do monitoramento
2. **Collector**: Componente intermediário que comunica com os dispositivos MikroTik
3. **MikroTik**: Dispositivos que executam os testes de conectividade

## Acessando os Dashboards

Após a configuração do sistema, você pode acessar os dashboards no Zabbix:

1. Acesse o frontend do Zabbix com suas credenciais
2. Navegue até **Monitoring** > **Dashboards**
3. Selecione um dos dashboards do Sentinel:
   - **Sentinel - Visão Geral**: Panorama de todos os dispositivos
   - **Sentinel - Detalhes do Dispositivo**: Informações detalhadas por dispositivo
   - **Sentinel - Análise por Destino**: Dados agrupados por IP alvo

## Interpretando os Dados

### Métricas de Ping

- **Latência (ms)**: Tempo médio de ida e volta dos pacotes
  - < 30ms: Excelente
  - 30-100ms: Bom
  - 100-200ms: Aceitável
  - > 200ms: Ruim/Problemático

- **Perda de Pacotes (%)**: Percentual de pacotes não recebidos
  - 0%: Ideal
  - 1-2%: Aceitável
  - > 2%: Indica problemas na rede

- **Jitter (ms)**: Variação da latência
  - < 10ms: Excelente
  - 10-30ms: Bom
  - > 30ms: Problemático para aplicações sensíveis como VoIP

### Métricas de TCP

- **Tempo de Conexão (ms)**: Tempo para estabelecer uma conexão TCP
  - < 100ms: Excelente
  - 100-300ms: Bom
  - > 300ms: Investigar possíveis problemas

- **Status**: Sucesso ou falha na conexão TCP

## Alertas e Notificações

O Sentinel gera alertas baseados em thresholds configuráveis:

1. **Alta Latência**: Quando a latência média excede o valor definido
2. **Perda de Pacotes**: Quando a porcentagem de perda excede o limite
3. **Alto Jitter**: Quando o jitter ultrapassa o valor configurado
4. **Falha na Conexão TCP**: Quando um serviço TCP não responde
5. **Tempo Elevado de Conexão TCP**: Quando o tempo de estabelecimento de conexão é alto

Você receberá notificações conforme configurado no Zabbix (email, SMS, webhook, etc.).

## Analisando Problemas

Quando um alerta é gerado, siga estes passos para análise:

1. Verifique o dashboard específico do dispositivo para entender o contexto
2. Analise os gráficos históricos para identificar padrões ou degradação gradual
3. Compare os resultados de diferentes dispositivos para o mesmo alvo
4. Verifique a infraestrutura de rede entre o dispositivo MikroTik e o alvo
5. Consulte os logs do collector para informações detalhadas sobre os testes

## Adicionando Novos Alvos de Monitoramento

Para adicionar um novo alvo para monitoramento:

1. Acesse **Configuration** > **Hosts** no Zabbix
2. Selecione o host (dispositivo MikroTik) desejado
3. Vá para a aba **Macros**
4. Atualize ou adicione a macro `{$TARGET_IP}` com o novo endereço
5. Alternativamente, para múltiplos alvos, crie macros como `{$TARGET_IP_1}`, `{$TARGET_IP_2}`
6. Atualize os itens HTTP Agent conforme necessário

## Personalizando Thresholds

Para personalizar os limites de alerta:

1. Acesse **Configuration** > **Hosts** no Zabbix
2. Selecione o host desejado
3. Vá para a aba **Macros**
4. Atualize as macros de threshold:
   - `{$HIGH_LATENCY_THRESHOLD}`
   - `{$HIGH_LOSS_THRESHOLD}`
   - `{$HIGH_JITTER_THRESHOLD}`
   - `{$HIGH_TCP_TIME_THRESHOLD}`

## Visualizando Histórico e Tendências

Para analisar o histórico de um indicador específico:

1. Navegue até **Monitoring** > **Latest data**
2. Selecione o host e localize o item desejado
3. Clique em **Graph** para visualizar o gráfico histórico
4. Use os controles de zoom e período para ajustar a visualização

## Exportando Dados

Para exportar dados de monitoramento:

1. Navegue até o gráfico desejado
2. Use a opção de exportação (CSV, XML, JSON) disponível no menu de contexto
3. Alternativamente, use a API do Zabbix para extrair dados programaticamente

## Manutenção Programada

Para evitar alertas durante manutenções programadas:

1. Navegue até **Configuration** > **Maintenance**
2. Clique em **Create maintenance period**
3. Configure o período de manutenção e selecione os hosts
4. Escolha os tipos de dados a serem coletados durante a manutenção

## Solução de Problemas Comuns

### Sem Dados de Monitoramento

- Verifique se o collector está em execução: `docker ps`
- Confirme a conectividade entre Zabbix e collector
- Verifique as credenciais do MikroTik nas macros

### Alertas Falsos Positivos

- Ajuste os thresholds nas macros do host
- Aumente o número de pacotes de ping para reduzir o impacto de outliers
- Configure períodos de manutenção durante janelas de instabilidade conhecida

### Latência ou Perda de Pacotes Elevada

- Verifique a conexão Internet do MikroTik
- Analise a rota de rede até o destino usando traceroute
- Compare resultados de diferentes MikroTiks para o mesmo alvo

### Falha na Conexão TCP

- Confirme se a porta está correta na macro `{$TCP_PORT}`
- Verifique se o serviço está em execução no alvo
- Confirme que não há firewalls bloqueando a conexão

## Suporte e Assistência

Em caso de problemas ou dúvidas:

1. Consulte a documentação completa no diretório `docs/`
2. Verifique os logs do collector: `docker-compose logs collector`
3. Entre em contato com a equipe de suporte através do portal de suporte ou email