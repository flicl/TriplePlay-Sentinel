# TriplePlay-Sentinel - Configuration de URLs e Links

Este arquivo centraliza todas as URLs e links utilizados na documentação do projeto para facilitar manutenção e atualizações.

## 🔗 Repositório Principal

- **GitHub Repository**: `https://github.com/tripleplay-dev/TriplePlay-Sentinel`
- **Docker Hub**: `https://hub.docker.com/r/tripleplay-dev/tripleplay-sentinel`
- **Git Clone URL**: `https://github.com/tripleplay-dev/TriplePlay-Sentinel.git`

## 🌐 URLs de API e Endpoints

### Desenvolvimento Local
- **Base URL**: `http://localhost:5000`
- **Health Check**: `http://localhost:5000/api/health`
- **Status**: `http://localhost:5000/api/status`
- **Dashboard**: `http://localhost:5000/dashboard`
- **API Test Endpoint**: `http://localhost:5000/api/test`

### Endpoints da API
- **Health**: `/api/health`
- **Status**: `/api/status`
- **Test**: `/api/test`
- **Connection Test**: `/api/connection-test`
- **Cache Metrics**: `/api/cache/metrics`
- **Cache Clear**: `/api/cache` (DELETE)

## 📚 Links de Documentação

### Estrutura Interna
- **Main Docs**: `docs/`
- **API Docs**: `docs/api/`
- **Guides**: `docs/guides/`
- **Architecture**: `docs/architecture/`
- **Security**: `docs/security/`
- **Troubleshooting**: `docs/troubleshooting/`

### Links Específicos
- **Quick Start**: `docs/guides/quick_start.md`
- **Docker Setup**: `docs/guides/docker_setup.md`
- **Docker Build Guide**: `docs/guides/docker_build_and_run.md`
- **MikroTik Setup**: `docs/guides/mikrotik_setup.md`
- **Zabbix Configuration**: `docs/zabbix/ZABBIX_CONFIGURATION.md`
- **API Reference**: `docs/api/collector_api.md`
- **Contributing**: `docs/contributing/CONTRIBUTING.md`
- **Troubleshooting**: `docs/troubleshooting/README.md`
- **Changelog**: `docs/changelog/CHANGELOG.md`

## 🐳 Docker

### Imagens
- **Main Image**: `tripleplay-dev/tripleplay-sentinel:latest`
- **Redis Image**: `redis:7-alpine`

### Containers
- **Main Container**: `tripleplay-sentinel`
- **Redis Container**: `tripleplay-redis`
- **Network**: `tripleplay-network`

## 📦 Templates e Recursos

### Zabbix Templates
- **Template Path**: `templates/zabbix/tripleplay-sentinel-template.yml`
- **Examples**: `templates/zabbix/examples/`

### Raw GitHub URLs
- **Template Download**: `https://raw.githubusercontent.com/tripleplay-dev/TriplePlay-Sentinel/main/templates/zabbix/tripleplay-sentinel-template.yml`

## 🔧 Desenvolvimento

### Repositório URLs
- **Clone HTTPS**: `https://github.com/tripleplay-dev/TriplePlay-Sentinel.git`
- **Clone SSH**: `git@github.com:tripleplay-dev/TriplePlay-Sentinel.git`
- **Issues**: `https://github.com/tripleplay-dev/TriplePlay-Sentinel/issues`
- **Discussions**: `https://github.com/tripleplay-dev/TriplePlay-Sentinel/discussions`
- **Pull Requests**: `https://github.com/tripleplay-dev/TriplePlay-Sentinel/pulls`

## 🌍 External Resources

### Standards e Specifications
- **Conventional Commits**: `https://www.conventionalcommits.org/`
- **Semantic Versioning**: `https://semver.org/`
- **MIT License**: `https://opensource.org/licenses/MIT`

### Related Tools
- **Docker**: `https://www.docker.com/`
- **Zabbix**: `https://www.zabbix.com/`
- **MikroTik**: `https://mikrotik.com/`
- **Redis**: `https://redis.io/`

## 📋 Checklist para Atualizações

Quando atualizar URLs do projeto, verificar os seguintes arquivos:

### Arquivos Principais
- [ ] `/README.md`
- [ ] `/docs/README.md`
- [ ] `/docs/INDEX.md`

### Guias de Instalação
- [ ] `/docs/guides/quick_start.md`
- [ ] `/docs/guides/docker_setup.md`
- [ ] `/docs/guides/docker_build_and_run.md`
- [ ] `/docs/guides/mikrotik_setup.md`

### Documentação Técnica
- [ ] `/docs/api/collector_api.md`
- [ ] `/docs/architecture/system_architecture.md`
- [ ] `/docs/contributing/CONTRIBUTING.md`

### Templates e Exemplos
- [ ] `/templates/zabbix/README.md`
- [ ] `/templates/zabbix/examples/*.md`

### Source Code
- [ ] `/src/collector/README.md`

### Release e Changelog
- [ ] `/docs/releases/RELEASE_NOTES_*.md`
- [ ] `/docs/changelog/CHANGELOG.md`

## 🔄 Comandos de Busca para Links

```bash
# Buscar links do GitHub
grep -r "github.com" docs/ --include="*.md"

# Buscar localhost URLs
grep -r "localhost:5000" docs/ --include="*.md"

# Buscar links relativos
grep -r "\[.*\](.*\.md)" docs/ --include="*.md"

# Buscar URLs HTTP
grep -r "http://" docs/ --include="*.md"

# Buscar URLs HTTPS
grep -r "https://" docs/ --include="*.md"
```

---

*Arquivo criado em: 28 de junho de 2025*
*Última atualização: Links atualizados para repositório oficial*