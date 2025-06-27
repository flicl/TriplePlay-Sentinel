# 📚 Documentação TriplePlay-Sentinel v2.1.0

**Versão:** 2.1.0 | **Status:** ✅ Production Ready | **Atualizado:** 23/06/2025

---

## 📖 Índice de Documentação

### 🚀 Início Rápido
- [README Principal](../README.md) - Visão geral e quick start
- [Guia de Instalação Rápida](guides/quick_start.md)
- [Docker Setup](guides/docker_setup.md)
- [Docker Build & Run](guides/docker_build_and_run.md) - Guia completo de build e execução manual

### 🎯 Zabbix Integration
- [Template Principal](../templates/zabbix/README.md)
- [Configuração Zabbix](zabbix/ZABBIX_CONFIGURATION.md)
- [Guia de Importação](../templates/zabbix/examples/import-guide.md)
- [Configuração de Hosts](../templates/zabbix/examples/host-configuration.md)

### 🔧 Configuração e Setup
- [Configuração MikroTik](guides/mikrotik_setup.md)
- [Configuração Zabbix](guides/zabbix_configuration.md)

### 🏗️ Arquitetura
- [Visão Geral do Sistema](architecture/system_architecture.md)
- [Cache Architecture](architecture/cache_architecture.md)
- [Visão Geral do Projeto](PROJECT_OVERVIEW.md)

### 📡 APIs e Integrações
- [API do Collector](api/collector_api.md)
- [Integração RouterOS](api/routeros_integration.md)
- [Zabbix HTTP Agent](api/zabbix_http_agent.md)

### 🛡️ Segurança
- [Diretrizes de Segurança](security/security_guidelines.md)

### 🔍 Troubleshooting
- [Guia de Resolução](troubleshooting/README.md)

### 📜 Histórico
- [Status de Desenvolvimento](../DEVELOPMENT_STATUS.md)
- [Release Notes v2.1.0](../RELEASE_NOTES_v2.1.0.md)
- [Histórico de Cleanup](cleanup-history/) - Documentação do processo de limpeza

---

## 🎯 Funcionalidades Principais (v2.1.0)

### ✅ Monitoramento Ativo
- **ICMP Ping Tests**: Latência, jitter, perda de pacotes, disponibilidade
- **Traceroute Analysis**: Análise de rota com contagem de hops
- **Network Quality Score**: Cálculo automático de qualidade de rede
- **Collector Health**: Status e performance do collector
- **Cache Metrics**: Métricas de hit/miss do cache
- **MikroTik Integration**: Status de conexão SSH

### 📊 Dashboard e Visualização
- **Network Overview Dashboard**: Dashboard principal de monitoramento
- **Performance Graphs**: Gráficos de RTT, perda de pacotes e jitter
- **Quality Metrics**: Scores e trends de qualidade de rede
- **System Health**: Monitoramento do collector e infraestrutura

### ⚙️ Compatibilidade
- **Zabbix Server**: 6.0+
- **Collector**: TriplePlay-Sentinel v2.0.0+
- **MikroTik RouterOS**: 6.0+
- **Python**: 3.9+ (para collector)

---

## 📋 Mudanças na v2.1.0

### ❌ Removido (Cleanup)
- **TCP Connection Monitoring**: Todos os items, triggers e widgets TCP
- **TCP Services Status Widget**: Widget de dashboard não funcional
- **TCP Connection Time Graph**: Gráfico de performance TCP
- **Referências órfãs**: Todas as referências quebradas eliminadas

### ✅ Melhorias
- **Template otimizado**: Tamanho significativamente reduzido
- **Clareza aprimorada**: Apenas funcionalidades implementadas
- **Performance**: Processamento mais rápido do template
- **Documentação**: 100% atualizada e consistente

---

## 🚀 Como Começar

### 1. **Instalação Rápida**
```bash
# Clone o repositório
git clone <repository-url>
cd TriplePlay-Sentinel

# Inicie com Docker
docker-compose up --build -d

# Ou execute localmente
./start_local.sh
```

### 2. **Configuração Zabbix**
```bash
# Importe o template
# Configuration → Templates → Import
# Arquivo: templates/zabbix/tripleplay-sentinel-template.yml
```

### 3. **Configuração de Host**
- Configure macros do MikroTik
- Defina targets de teste
- Ajuste thresholds conforme necessário

---

## 📞 Suporte e Comunidade

- **Documentação**: Diretório `/docs/`
- **Issues**: GitHub Issues tracker
- **Configuração**: Guias em `/docs/guides/`
- **API Reference**: `/docs/api/`

---

**Equipe:** TriplePlay Development Team  
**Licença:** [Sua Licença]  
**Repositório:** [URL do Repositório]