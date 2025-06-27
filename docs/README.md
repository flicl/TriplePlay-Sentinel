# 📚 TriplePlay-Sentinel - Documentação

**Versão:** 2.1.0 | **Status:** ✅ Limpo e Organizado | **Atualizado:** 23/06/2025

---

## 🎯 Visão Geral

Documentação completa do TriplePlay-Sentinel, um sistema de monitoramento especializado para integração Zabbix-MikroTik via HTTP Agent (PULL).

> **💡 Para navegação rápida**, consulte o [**Índice Principal**](INDEX.md) que contém todos os links organizados.

---

## 📁 Estrutura da Documentação

### 🚀 **Início Rápido**
- [**README Principal**](../README.md) - Visão geral e quick start do projeto
- [**Quick Start Guide**](guides/quick_start.md) - Começar em 15 minutos
- [**Docker Setup**](guides/docker_setup.md) - Instalação com Docker

### 🎯 **Zabbix Integration**
- [**Template Zabbix**](../templates/zabbix/README.md) - Template v2.1.0 limpo
- [**Configuração Zabbix**](zabbix/ZABBIX_CONFIGURATION.md) - Setup detalhado
- [**Guia de Importação**](../templates/zabbix/examples/import-guide.md) - Passo a passo
- [**Configuração de Hosts**](../templates/zabbix/examples/host-configuration.md) - Multi-site

### 🏗️ **Arquitetura**
- [**Visão Geral do Sistema**](architecture/system_architecture.md) - Arquitetura completa
- [**Cache Architecture**](architecture/cache_architecture.md) - Sistema de cache
- [**Project Overview**](PROJECT_OVERVIEW.md) - Visão geral técnica

### 📡 **APIs e Integrações**
- [**Collector API**](api/collector_api.md) - API REST completa
- [**RouterOS Integration**](api/routeros_integration.md) - Integração MikroTik
- [**Zabbix HTTP Agent**](api/zabbix_http_agent.md) - Configuração HTTP Agent

### ⚙️ **Configuração**
- [**MikroTik Setup**](guides/mikrotik_setup.md) - Preparação dos dispositivos
- [**Zabbix Configuration**](guides/zabbix_configuration.md) - Configuração Zabbix

### 🛡️ **Segurança**
- [**Security Guidelines**](security/security_guidelines.md) - Diretrizes de segurança

### 🔍 **Troubleshooting**
- [**Guia de Resolução**](troubleshooting/README.md) - Problemas comuns e soluções

### 📜 **Histórico**
- [**Development Status**](../DEVELOPMENT_STATUS.md) - Status atual do projeto
- [**Release Notes v2.1.0**](../RELEASE_NOTES_v2.1.0.md) - Notas da versão atual
- [**Cleanup History**](cleanup-history/) - Histórico do processo de limpeza

---

## 👥 Guias por Perfil de Usuário

### 👨‍💼 **Administradores de Sistema**
1. [README Principal](../README.md) → [Quick Start](guides/quick_start.md)
2. [Template Zabbix](../templates/zabbix/README.md) → [Configuração](zabbix/ZABBIX_CONFIGURATION.md)
3. [Troubleshooting](troubleshooting/README.md)

### 🔧 **Operadores de Rede**
1. [Guia de Importação](../templates/zabbix/examples/import-guide.md)
2. [Configuração de Hosts](../templates/zabbix/examples/host-configuration.md)
3. [API Reference](api/collector_api.md)

### 👨‍💻 **Desenvolvedores**
1. [System Architecture](architecture/system_architecture.md)
2. [Collector API](api/collector_api.md) → [RouterOS Integration](api/routeros_integration.md)
3. [Development Status](../DEVELOPMENT_STATUS.md)

### 🛡️ **Security Officers**
1. [Security Guidelines](security/security_guidelines.md)
2. [System Architecture](architecture/system_architecture.md)

---

## 🧹 Estrutura Limpa (v2.1.0)

Esta documentação foi **reorganizada e limpa** na versão 2.1.0:

### ✅ **Mantido**
- Documentação essencial e funcional
- Guias práticos de instalação e configuração
- Referências de API e arquitetura
- Histórico importante (movido para `cleanup-history/`)

### ❌ **Removido**
- Documentação obsoleta e desatualizada
- Diretórios vazios
- Arquivos temporários e de teste
- Referências a funcionalidades não implementadas

### 📈 **Benefícios**
- **Navegação mais fácil**: Estrutura lógica e clara
- **Manutenção simplificada**: Menos arquivos desnecessários
- **Onboarding rápido**: Informações organizadas
- **Produção ready**: Apenas conteúdo relevante

---

## 📞 Suporte

- **Índice Completo**: [INDEX.md](INDEX.md)
- **Issues**: GitHub Issues tracker
- **API Reference**: [Collector API](api/collector_api.md)
- **Quick Start**: [Guia Rápido](guides/quick_start.md)

---

**Equipe:** TriplePlay Development Team  
**Licença:** [Sua Licença]  
**Repositório:** [URL do Repositório]