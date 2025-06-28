#!/bin/bash

# TriplePlay-Sentinel API-Only Collector - Start Script
# Sistema de Monitoramento 100% baseado na API MikroTik (sem SSH)

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função de log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Banner
echo -e "${BLUE}"
echo "========================================================"
echo "  TriplePlay-Sentinel API-Only Collector v2.0.0"
echo "  Sistema 100% API MikroTik (Zero SSH Dependencies)"
echo "========================================================"
echo -e "${NC}"

# Verifica se está no diretório correto
if [ ! -f "app_api_only.py" ]; then
    error "app_api_only.py não encontrado. Execute o script no diretório correto."
    exit 1
fi

# Configurações padrão
export COLLECTOR_HOST="${COLLECTOR_HOST:-0.0.0.0}"
export COLLECTOR_PORT="${COLLECTOR_PORT:-5000}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export CACHE_TTL="${CACHE_TTL:-30}"
export MAX_CONCURRENT_HOSTS="${MAX_CONCURRENT_HOSTS:-50}"
export MAX_CONCURRENT_COMMANDS="${MAX_CONCURRENT_COMMANDS:-20}"
export MIKROTIK_USE_SSL="${MIKROTIK_USE_SSL:-true}"
export MIKROTIK_API_PORT="${MIKROTIK_API_PORT:-8728}"

log "Configurações da aplicação:"
info "  Host: $COLLECTOR_HOST"
info "  Porta: $COLLECTOR_PORT"
info "  Log Level: $LOG_LEVEL"
info "  Cache TTL: ${CACHE_TTL}s"
info "  Max Hosts Concorrentes: $MAX_CONCURRENT_HOSTS"
info "  Max Comandos Concorrentes: $MAX_CONCURRENT_COMMANDS"
info "  MikroTik SSL: $MIKROTIK_USE_SSL"
info "  MikroTik API Port: $MIKROTIK_API_PORT"

# Verifica Python
if ! command -v python3 &> /dev/null; then
    error "Python3 não encontrado. Instale Python 3.8+ para continuar."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
log "Usando Python $PYTHON_VERSION"

# Verifica dependências
log "Verificando dependências..."
if [ -f "requirements_api_only.txt" ]; then
    if ! python3 -c "import aiohttp, flask" &> /dev/null; then
        warn "Dependências não encontradas. Instalando..."
        pip3 install -r requirements_api_only.txt
    else
        info "Dependências OK"
    fi
else
    warn "requirements_api_only.txt não encontrado"
fi

# Verifica conectividade de rede
log "Verificando conectividade..."
if command -v ping &> /dev/null; then
    if ping -c 1 8.8.8.8 &> /dev/null; then
        info "Conectividade de rede OK"
    else
        warn "Conectividade limitada - alguns testes podem falhar"
    fi
fi

# Cria diretório de logs se não existir
mkdir -p logs

# Função de cleanup
cleanup() {
    log "Encerrando TriplePlay-Sentinel API-Only Collector..."
    if [ ! -z "$APP_PID" ]; then
        kill $APP_PID 2>/dev/null || true
        wait $APP_PID 2>/dev/null || true
    fi
    log "Aplicação encerrada"
    exit 0
}

# Registra função de cleanup
trap cleanup SIGINT SIGTERM

# Inicia aplicação
log "Iniciando TriplePlay-Sentinel API-Only Collector..."
info "Pressione Ctrl+C para parar"

# Executa em modo daemon se especificado
if [ "$1" = "--daemon" ] || [ "$1" = "-d" ]; then
    log "Executando em modo daemon..."
    nohup python3 app_api_only.py > logs/app.log 2>&1 &
    APP_PID=$!
    echo $APP_PID > logs/app.pid
    log "Aplicação iniciada com PID $APP_PID"
    log "Logs: tail -f logs/app.log"
    log "Para parar: kill $APP_PID"
else
    # Executa em modo interativo
    python3 app_api_only.py &
    APP_PID=$!
    
    # Aguarda a aplicação inicializar
    sleep 2
    
    # Testa se a aplicação está funcionando
    if kill -0 $APP_PID 2>/dev/null; then
        log "Aplicação iniciada com sucesso!"
        info "API disponível em: http://$COLLECTOR_HOST:$COLLECTOR_PORT"
        info "Health check: http://$COLLECTOR_HOST:$COLLECTOR_PORT/health"
        info "Estatísticas: http://$COLLECTOR_HOST:$COLLECTOR_PORT/api/v2/stats"
        echo ""
        info "Endpoints principais:"
        info "  POST /api/v2/mikrotik/ping - Ping via API MikroTik"
        info "  POST /api/v2/mikrotik/command - Comando genérico"
        info "  POST /api/v2/mikrotik/batch - Múltiplos comandos paralelos"
        info "  POST /api/v2/mikrotik/multi-host - Múltiplos hosts paralelos"
        info "  POST /api/v2/test-connection - Teste de conectividade"
        echo ""
        warn "MODO: API-Only (100% MikroTik API, sem SSH)"
        
        # Aguarda encerramento
        wait $APP_PID
    else
        error "Falha ao iniciar a aplicação"
        exit 1
    fi
fi
