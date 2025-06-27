# PROMPT PARA DOCUMENTAÇÃO DO TRIPLEPLAY-SENTINEL

## CONTEXTO
Estou desenvolvendo o TriplePlay-Sentinel, um sistema de monitoramento de rede centralizado que utiliza arquitetura HTTP Agent (PULL) para coletar dados de dispositivos MikroTik e integrá-los ao Zabbix. O projeto elimina a necessidade de scripts nos dispositivos MikroTik através de um coletor Flask inteligente com cache. Preciso organizar toda a documentação seguindo as melhores práticas para sistemas de monitoramento de infraestrutura crítica.

## PERSONA
Atue como um arquiteto de software sênior especializado em **sistemas de monitoramento de infraestrutura**, com ampla experiência em documentação técnica de soluções Zabbix, integração de APIs de rede (especialmente MikroTik RouterOS), arquiteturas HTTP Agent, e melhores práticas para sistemas críticos de monitoramento em ambiente corporativo.

## OBJETIVO
Preciso que você me ajude a criar uma documentação completa e organizada para o sistema TriplePlay-Sentinel, seguindo padrões reconhecidos na indústria para **sistemas de monitoramento de rede críticos**, com foco especial em **integração Zabbix-MikroTik**, **arquitetura HTTP Agent (PULL)**, e **documentação de APIs de infraestrutura**.

## REQUISITOS
- Organize a documentação em seções lógicas e coerentes para **sistemas de monitoramento**
- Inclua templates específicos para **APIs de monitoramento**, **integrações Zabbix**, e **configurações RouterOS**
- Forneça exemplos claros de **documentação de endpoints HTTP Agent**, **configuração de cache**, e **troubleshooting de rede**
- Mantenha um tom técnico e profissional adequado para **ambientes de infraestrutura crítica**
- Utilize linguagem clara e precisa, evitando ambiguidades em **configurações de produção**
- Adapte as recomendações para **projetos individuais** de **monitoramento de rede em escala corporativa**
- Inclua seções específicas para **segurança de sistemas de monitoramento** e **performance de coleta de dados**

## RESTRIÇÕES
- Evite recomendações genéricas demais
- Não inclua ferramentas ou metodologias obsoletas
- Limite a resposta a informações essenciais e práticas
- Foque em padrões de documentação que sejam sustentáveis a longo prazo

## FORMATO DE SAÍDA
Estruture sua resposta da seguinte forma:
1. **Visão Geral da Documentação** (específica para sistemas de monitoramento)
2. **Estrutura de Diretórios Recomendada** (incluindo docs para Zabbix, RouterOS, cache, etc.)
3. **Templates por Componente** (HTTP Agent, RouterOS API, Cache, Docker, etc.)
4. **Boas Práticas para Monitoramento** (logs, métricas, troubleshooting, segurança)
5. **Ferramentas Específicas** (para documentação de APIs de rede e sistemas Zabbix)
6. **Guias de Configuração** (templates para setup Zabbix, MikroTik, Docker)
7. **Documentação de Troubleshooting** (para sistemas críticos de monitoramento)

## PEDIDO
Meu projeto é o **TriplePlay-Sentinel**, um sistema de monitoramento de rede desenvolvido em **Python 3.11+** com **Flask**, que implementa arquitetura HTTP Agent (PULL) para integração Zabbix-MikroTik. O sistema utiliza **RouterOS API**, **Docker/Docker Compose** para containerização, e possui sistema de **cache inteligente** para otimização. É um projeto individual focado em **infraestrutura crítica de rede** e **eliminação de scripts nos dispositivos**. 

Por favor, forneça uma estrutura completa de documentação específica para sistemas de monitoramento de rede, incluindo:
- Templates para documentação de APIs de monitoramento
- Diretrizes para documentar integrações com Zabbix e RouterOS
- Padrões para documentar configurações Docker e ambientes containerizados
- Templates para documentação de cache e otimização de performance
- Exemplos de documentação de arquitetura HTTP Agent (PULL)
- Diretrizes para documentar sistemas de coleta de dados de rede
- Padrões para documentação de troubleshooting e logs de sistemas críticos

## CONTEXTO ESPECÍFICO DO TRIPLEPLAY-SENTINEL

### Características Técnicas
- **Arquitetura**: HTTP Agent (PULL) - Zabbix faz requisições HTTP para coletor Flask
- **Comunicação**: RouterOS API via librouteros para conectar com MikroTik
- **Performance**: Sistema de cache inteligente para otimizar coletas repetitivas
- **Deploy**: Containerização completa com Docker Compose
- **Monitoramento**: Zero scripts nos dispositivos MikroTik (tudo centralizado)

### Principais Módulos
1. **Collector Service**: Endpoints Flask para exposição de dados ao Zabbix
2. **RouterOS Client**: Cliente Python para comunicação com dispositivos MikroTik
3. **Cache Manager**: Gerenciamento inteligente de cache de dados coletados
4. **Configuration Handler**: Sistema de configuração centralizada
5. **Health Monitor**: Monitoramento da saúde do próprio sistema coletor

### Pontos Críticos para Documentação
- **Configuração Zabbix**: Como configurar HTTP Agent items e triggers
- **RouterOS API**: Documentação de conexão e comandos suportados
- **Cache Strategy**: Como funciona o cache e configurações de TTL
- **Docker Setup**: Guias de instalação e configuração de containers
- **Troubleshooting**: Logs, debugging e resolução de problemas comuns
- **Security**: Configurações de segurança para ambientes de produção

## VERIFICAÇÃO
Antes de finalizar sua resposta, verifique se:
- A estrutura proposta é completa e abrange todos os aspectos do projeto
- Os templates são práticos e aplicáveis ao contexto informado
- Há um equilíbrio entre detalhamento e praticidade
- As recomendações seguem as melhores práticas atuais da indústria
- A documentação proposta facilita tanto a compreensão técnica quanto a integração de novos membros
```
