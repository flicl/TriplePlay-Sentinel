# Guia de Troubleshooting do Sentinel

Este guia fornece instruções para diagnosticar e resolver problemas comuns no sistema Sentinel.

## Problemas de Instalação

### O Docker Compose não Inicia

**Sintomas:**
- Erro ao executar `docker-compose up -d`
- O container não aparece na lista de `docker ps`

**Verificações:**
1. Verifique os logs detalhados do Docker Compose:
   ```bash
   docker-compose up
   ```

2. Confirme que as portas não estão em uso:
   ```bash
   sudo netstat -tulpn | grep 8000
   ```

3. Verifique se o arquivo `.env` foi configurado corretamente:
   ```bash
   cat .env
   ```

**Soluções:**
- Se houver conflito de portas, altere a porta no arquivo `docker-compose.yml`
- Se houver problemas com variáveis de ambiente, verifique o formato do arquivo `.env`
- Tente reconstruir a imagem: `docker-compose build --no-cache`

### Erro ao Construir a Imagem Docker

**Sintomas:**
- Falha ao executar `docker-compose build`
- Erros relacionados a pacotes ou dependências

**Verificações:**
1. Verifique os logs de construção:
   ```bash
   docker-compose build --no-cache
   ```

2. Confirme que o Dockerfile está correto:
   ```bash
   cat Dockerfile
   ```

**Soluções:**
- Atualize o sistema operacional: `apt update && apt upgrade`
- Verifique a conexão com a internet para baixar pacotes
- Corrija problemas no Dockerfile, se necessário

## Problemas de Comunicação

### Collector não Responde ao Zabbix

**Sintomas:**
- Itens "No data" no Zabbix
- Erro "Cannot connect" nos logs do Zabbix

**Verificações:**
1. Verifique se o collector está em execução:
   ```bash
   docker ps
   ```

2. Teste a conectividade básica:
   ```bash
   curl -X GET http://localhost:8000/healthcheck
   ```

3. Verifique os logs do collector:
   ```bash
   docker-compose logs collector
   ```

4. Teste se o Zabbix Server pode acessar o collector:
   ```bash
   # Executar no servidor Zabbix
   curl -X GET http://collector-ip:8000/healthcheck
   ```

**Soluções:**
- Reinicie o container do collector: `docker-compose restart collector`
- Verifique as regras de firewall entre Zabbix e collector
- Confirme que a URL do collector no Zabbix está correta
- Verifique se o token de autenticação corresponde ao configurado

### Collector não Consegue Conectar ao MikroTik

**Sintomas:**
- Resposta de erro do collector no Zabbix: "Failed to connect to MikroTik"
- Logs indicando falha de conexão API ou SSH

**Verificações:**
1. Teste a conectividade do collector para o MikroTik:
   ```bash
   # Entre no container do collector
   docker-compose exec collector bash
   ping mikrotik-ip
   ```

2. Verifique as credenciais do MikroTik nas macros do Zabbix:
   - `{$MIKROTIK_IP}`
   - `{$MIKROTIK_USER}`
   - `{$MIKROTIK_PASSWORD}`
   - `{$MIKROTIK_PORT}`

3. Confirme que o API ou SSH está habilitado no MikroTik:
   ```bash
   # Via terminal do MikroTik
   /ip service print
   ```

**Soluções:**
- Corrija as credenciais nas macros do Zabbix
- Habilite o serviço API ou SSH no MikroTik:
   ```bash
   # Para API
   /ip service enable api
   # Para SSH
   /ip service enable ssh
   ```
- Verifique as regras de firewall no MikroTik:
   ```bash
   /ip firewall filter print
   ```

## Problemas com os Testes

### Falha nos Testes de Ping

**Sintomas:**
- Resposta JSON indicando erro no teste de ping
- Status "Failed" no item "Sentinel - Ping Status"

**Verificações:**
1. Verifique os logs do collector para ver o comando exato e o erro:
   ```bash
   docker-compose logs collector | grep -i ping
   ```

2. Teste manualmente um ping do MikroTik para o alvo:
   ```bash
   # Via terminal do MikroTik
   /ping target-ip count=4
   ```

3. Verifique as permissões do usuário no MikroTik:
   ```bash
   # Via terminal do MikroTik
   /user group print
   ```

**Soluções:**
- Corrija o endereço IP alvo (`{$TARGET_IP}`)
- Verifique se o MikroTik tem conectividade com o alvo
- Ajuste os parâmetros de ping (`{$PING_COUNT}`, `{$PING_TIMEOUT}`)
- Conceda permissões adequadas ao usuário no MikroTik

### Falha nos Testes de TCP

**Sintomas:**
- Resposta JSON indicando erro na conexão TCP
- Status "Failed" no item "Sentinel - TCP Connection Status"

**Verificações:**
1. Verifique os logs do collector para detalhes do erro:
   ```bash
   docker-compose logs collector | grep -i tcp
   ```

2. Teste manualmente uma conexão TCP do MikroTik:
   ```bash
   # Via terminal do MikroTik
   /tool fetch url=tcp://target-ip:port
   ```

3. Verifique se a porta está correta na macro `{$TCP_PORT}`

**Soluções:**
- Corrija o endereço IP alvo e a porta TCP
- Verifique se o serviço alvo está em execução
- Confirme que não há firewalls bloqueando a porta
- Ajuste o timeout do teste se o alvo for de alta latência

## Problemas no Zabbix

### Erros de Pré-processamento

**Sintomas:**
- "Cannot parse JSON" nos itens HTTP Agent
- Valores incorretos ou ausentes nos itens dependentes

**Verificações:**
1. Verifique o valor bruto recebido pelo item mestre:
   - Vá para o item HTTP Agent no Zabbix
   - Clique na "Latest data" e examine o valor

2. Teste a requisição manualmente:
   ```bash
   curl -X POST http://collector-ip:8000/run_test \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer token" \
     -d '{"mikrotik_ip":"ip", "mikrotik_user":"user", ...}'
   ```

3. Verifique as expressões JSONPath nos itens dependentes

**Soluções:**
- Corrija a URL ou os parâmetros da requisição
- Ajuste as expressões JSONPath para os campos corretos
- Verifique se o formato de resposta do collector está correto

### Alertas Falsos

**Sintomas:**
- Muitos alertas sem problemas reais
- Triggers disparando frequentemente e se recuperando rapidamente

**Verificações:**
1. Analise os gráficos históricos para ver a volatilidade dos dados
2. Verifique os thresholds nas macros:
   - `{$HIGH_LATENCY_THRESHOLD}`
   - `{$HIGH_LOSS_THRESHOLD}`
   - `{$HIGH_JITTER_THRESHOLD}`
   - `{$HIGH_TCP_TIME_THRESHOLD}`

3. Verifique a configuração das triggers para condições de histerese

**Soluções:**
- Ajuste os thresholds para valores mais adequados
- Modifique as triggers para usar médias (`avg()`) ou requerir múltiplos valores consecutivos
- Aumente o número de pacotes de ping para obter médias mais estáveis

## Problemas de Performance

### Lentidão no Collector

**Sintomas:**
- Tempo de resposta alto do collector
- Timeout nos itens HTTP Agent do Zabbix

**Verificações:**
1. Verifique o uso de recursos do container:
   ```bash
   docker stats collector
   ```

2. Examine os logs em busca de erros ou atrasos:
   ```bash
   docker-compose logs collector | grep -i error
   docker-compose logs collector | grep -i timeout
   ```

3. Verifique o número de requisições simultâneas:
   ```bash
   # Se o collector roda em um host Linux
   netstat -an | grep :8000 | wc -l
   ```

**Soluções:**
- Aumente os recursos do container (CPU, memória)
- Ajuste o timeout dos itens HTTP Agent no Zabbix
- Revise o código do collector para otimização
- Considere implementar cache de conexões no collector
- Escale horizontalmente com múltiplas instâncias do collector

### Sobrecarga no MikroTik

**Sintomas:**
- Aumento no uso de CPU do MikroTik
- Lentidão geral do MikroTik durante os testes

**Verificações:**
1. Monitore o uso de recursos do MikroTik:
   ```bash
   # Via terminal do MikroTik
   /system resource print
   ```

2. Verifique a frequência das requisições do Zabbix

**Soluções:**
- Reduza a frequência de coleta no Zabbix (aumente o intervalo)
- Distribua os testes para diferentes MikroTiks
- Otimize os parâmetros de teste (reduza o número de pacotes)
- Atualize o RouterOS para versões mais eficientes

## Logs e Diagnóstico

### Aumentando o Nível de Log

Para obter mais informações de diagnóstico:

1. Altere o nível de log no arquivo `.env`:
   ```
   LOG_LEVEL=DEBUG
   ```

2. Reinicie o collector:
   ```bash
   docker-compose restart collector
   ```

3. Veja os logs detalhados:
   ```bash
   docker-compose logs --tail=100 collector
   ```

### Coletando Informações para Suporte

Se precisar contatar o suporte, reúna as seguintes informações:

1. Versão do sistema:
   ```bash
   docker-compose --version
   docker --version
   python --version
   ```

2. Logs do collector:
   ```bash
   docker-compose logs collector > collector_logs.txt
   ```

3. Configuração (removendo senhas):
   ```bash
   grep -v PASSWORD .env > env_sanitized.txt
   docker-compose config > compose_config.txt
   ```

4. Versão e detalhes do MikroTik:
   ```bash
   # Via terminal do MikroTik
   /system resource print
   /system package print
   ```

5. Capturas de tela dos erros no Zabbix

## Problemas Comuns e Soluções Rápidas

| Problema | Solução Rápida |
|----------|----------------|
| Container não inicia | `docker-compose down && docker-compose up -d` |
| Erro de autenticação | Verifique o token no `.env` e na configuração do Zabbix |
| Sem comunicação com MikroTik | Verifique credenciais e IP corretos nas macros |
| Dados JSON malformados | Verifique os logs do collector e o formato de resposta |
| Perda de conectividade intermitente | Aumente timeouts e implemente retries |
| Latência alta nos testes | Verifique se o MikroTik e o collector têm recursos suficientes |