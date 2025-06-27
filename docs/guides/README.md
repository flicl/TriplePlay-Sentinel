# 📖 Guias de Instalação e Configuração

Este diretório contém guias detalhados para diferentes cenários de instalação e configuração do TriplePlay-Sentinel.

## 📋 Guias Disponíveis

### 🐳 Docker
- **[docker_setup.md](docker_setup.md)** - Setup completo com Docker Compose
- **[docker_build_and_run.md](docker_build_and_run.md)** - Build manual e execução com `docker run`
- **[docker-enhanced-setup.md](docker-enhanced-setup.md)** - Configuração avançada

### ⚙️ Configuração
- **[quick_start.md](quick_start.md)** - Início rápido
- **[mikrotik_setup.md](mikrotik_setup.md)** - Configuração dos dispositivos MikroTik
- **[zabbix_configuration.md](zabbix_configuration.md)** - Configuração do Zabbix Server

## 🚀 Cenários de Uso

### 1. Desenvolvimento Local
```bash
# Opção 1: Com Docker Compose
docker-compose up -d

# Opção 2: Build manual
./docker-helper.sh build
./docker-helper.sh run-with-redis
```

### 2. Produção com Docker
```bash
# Seguir guia: docker_setup.md
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Instalação Manual
```bash
# Seguir guia: quick_start.md para setup local
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 🔧 Ferramentas Úteis

### Script Helper
O projeto inclui um script utilitário para facilitar operações Docker:

```bash
# Construir imagem
./docker-helper.sh build

# Executar com Redis
./docker-helper.sh run-with-redis

# Ver status
./docker-helper.sh status

# Ver logs
./docker-helper.sh logs

# Testar API
./docker-helper.sh test

# Limpar tudo
./docker-helper.sh clean
```

### Comandos Básicos

| Comando | Descrição |
|---------|-----------|
| `./docker-helper.sh help` | Mostra ajuda completa |
| `docker-compose ps` | Status dos serviços |
| `docker logs tripleplay-sentinel` | Logs do container |
| `curl http://localhost:5000/health` | Teste de saúde |

## 📚 Próximos Passos

Após a instalação:

1. **Configure o MikroTik** - [mikrotik_setup.md](mikrotik_setup.md)
2. **Configure o Zabbix** - [zabbix_configuration.md](zabbix_configuration.md)
3. **Importe os Templates** - [../templates/zabbix/examples/import-guide.md](../templates/zabbix/examples/import-guide.md)
4. **Configure Hosts** - [../templates/zabbix/examples/host-configuration.md](../templates/zabbix/examples/host-configuration.md)

## 🆘 Precisa de Ajuda?

- **Troubleshooting**: [../troubleshooting/README.md](../troubleshooting/README.md)
- **API Reference**: [../api/collector_api.md](../api/collector_api.md)
- **Issues**: Abra uma issue no repositório GitHub

---

**📧 Suporte:** Para dúvidas específicas, consulte o guia correspondente ou a documentação completa em [../INDEX.md](../INDEX.md)
