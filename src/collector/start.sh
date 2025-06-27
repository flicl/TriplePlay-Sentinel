#!/bin/bash
# TriplePlay-Sentinel Collector - Script de Inicialização
# Sistema de Monitoramento Centralizado MikroTik-Zabbix via HTTP Agent (PULL)

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Banner
cat << 'EOF'
🛡️  TriplePlay-Sentinel Collector v2.0
=============================================
Sistema de Monitoramento Centralizado
MikroTik-Zabbix via HTTP Agent (PULL)
=============================================
EOF

# Verificações iniciais
log "Verificando dependências..."

# Verifica Python
if ! command -v python3 &> /dev/null; then
    error "Python 3 não encontrado. Instale Python 3.8 ou superior."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d" " -f2)
log "Python ${PYTHON_VERSION} encontrado"

# Verifica pip
if ! command -v pip3 &> /dev/null; then
    error "pip3 não encontrado. Instale pip para Python 3."
    exit 1
fi

# Diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
log "Diretório do collector: ${SCRIPT_DIR}"

# Cria arquivo .env se não existir
if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    if [ -f "${SCRIPT_DIR}/.env.example" ]; then
        log "Criando arquivo .env a partir do exemplo..."
        cp "${SCRIPT_DIR}/.env.example" "${SCRIPT_DIR}/.env"
        warning "Configure o arquivo .env antes de executar em produção!"
    else
        warning "Arquivo .env.example não encontrado"
    fi
fi

# Carrega variáveis de ambiente
if [ -f "${SCRIPT_DIR}/.env" ]; then
    log "Carregando configurações do .env..."
    export $(cat "${SCRIPT_DIR}/.env" | grep -v '^#' | xargs)
fi

# Configurações padrão
COLLECTOR_HOST=${COLLECTOR_HOST:-"0.0.0.0"}
COLLECTOR_PORT=${COLLECTOR_PORT:-"5000"}
LOG_LEVEL=${LOG_LEVEL:-"INFO"}

# Função para instalar dependências
install_dependencies() {
    log "Instalando dependências Python..."
    
    # Verifica se requirements.txt existe
    if [ ! -f "${SCRIPT_DIR}/requirements.txt" ]; then
        error "Arquivo requirements.txt não encontrado"
        exit 1
    fi
    
    # Instala dependências
    pip3 install -r "${SCRIPT_DIR}/requirements.txt"
    
    success "Dependências instaladas com sucesso"
}

# Função para verificar conectividade
check_connectivity() {
    log "Verificando conectividade básica..."
    
    # Testa resolução DNS
    if ! nslookup google.com > /dev/null 2>&1; then
        warning "Resolução DNS pode estar com problemas"
    fi
    
    # Verifica se a porta está disponível
    if netstat -tuln 2>/dev/null | grep -q ":${COLLECTOR_PORT} "; then
        warning "Porta ${COLLECTOR_PORT} já está em uso"
    fi
}

# Função para executar o collector
run_collector() {
    log "Iniciando TriplePlay-Sentinel Collector..."
    log "Host: ${COLLECTOR_HOST}"
    log "Porta: ${COLLECTOR_PORT}"
    log "Log Level: ${LOG_LEVEL}"
    
    cd "${SCRIPT_DIR}"
    
    # Executa o collector
    exec python3 -u app.py
}

# Função para executar em modo de desenvolvimento
run_dev() {
    log "Executando em modo de desenvolvimento..."
    export FLASK_DEBUG=true
    export LOG_LEVEL=DEBUG
    export COLLECTOR_HOST=127.0.0.1
    
    run_collector
}

# Função para executar com gunicorn (produção)
run_production() {
    log "Executando em modo de produção com Gunicorn..."
    
    if ! command -v gunicorn &> /dev/null; then
        error "Gunicorn não encontrado. Instale com: pip3 install gunicorn"
        exit 1
    fi
    
    WORKERS=${GUNICORN_WORKERS:-4}
    TIMEOUT=${GUNICORN_TIMEOUT:-120}
    
    log "Workers: ${WORKERS}"
    log "Timeout: ${TIMEOUT}s"
    
    cd "${SCRIPT_DIR}"
    
    exec gunicorn \
        --workers=${WORKERS} \
        --timeout=${TIMEOUT} \
        --bind=${COLLECTOR_HOST}:${COLLECTOR_PORT} \
        --worker-class=gevent \
        --worker-connections=1000 \
        --max-requests=1000 \
        --max-requests-jitter=100 \
        --preload \
        --access-logfile=- \
        --error-logfile=- \
        --log-level=${LOG_LEVEL,,} \
        app:app
}

# Função para mostrar ajuda
show_help() {
    cat << EOF
Uso: $0 [COMANDO]

Comandos disponíveis:
    install     Instala dependências Python
    run         Executa o collector (desenvolvimento)
    start       Executa o collector (produção com Gunicorn)
    check       Verifica dependências e configurações
    help        Mostra esta ajuda

Variáveis de ambiente importantes:
    COLLECTOR_HOST      Interface de bind (padrão: 0.0.0.0)
    COLLECTOR_PORT      Porta do serviço (padrão: 5000)
    LOG_LEVEL          Nível de log (padrão: INFO)
    CACHE_TTL          TTL do cache em segundos (padrão: 30)

Exemplos:
    $0 install          # Instala dependências
    $0 run              # Executa em modo desenvolvimento
    $0 start            # Executa em modo produção
    $0 check            # Verifica configurações

EOF
}

# Parse dos argumentos
case "${1:-run}" in
    "install")
        install_dependencies
        ;;
    "run"|"dev")
        check_connectivity
        run_dev
        ;;
    "start"|"prod"|"production")
        check_connectivity
        run_production
        ;;
    "check")
        log "Verificando configurações..."
        check_connectivity
        
        if [ -f "${SCRIPT_DIR}/.env" ]; then
            success "Arquivo .env encontrado"
        else
            warning "Arquivo .env não encontrado"
        fi
        
        if [ -f "${SCRIPT_DIR}/requirements.txt" ]; then
            success "Arquivo requirements.txt encontrado"
        else
            error "Arquivo requirements.txt não encontrado"
        fi
        
        success "Verificações concluídas"
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        error "Comando desconhecido: $1"
        show_help
        exit 1
        ;;
esac