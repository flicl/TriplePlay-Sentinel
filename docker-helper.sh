#!/bin/bash

# 🐳 TriplePlay-Sentinel Docker Helper Script
# Script utilitário para build e execução do container Docker

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações padrão
IMAGE_NAME="tripleplay-sentinel"
IMAGE_TAG="latest"
CONTAINER_NAME="tripleplay-sentinel"
REDIS_CONTAINER_NAME="tripleplay-redis"
NETWORK_NAME="tripleplay-network"
PORT="5000"
LOGS_DIR="/opt/tripleplay-sentinel/logs"

# Função para exibir ajuda
show_help() {
    echo -e "${BLUE}🐳 TriplePlay-Sentinel Docker Helper${NC}"
    echo -e "${BLUE}=====================================${NC}"
    echo ""
    echo "Uso: $0 [COMANDO] [OPÇÕES]"
    echo ""
    echo "COMANDOS:"
    echo "  build                 Constrói a imagem Docker"
    echo "  run                   Executa o container (standalone)"
    echo "  run-with-redis        Executa com Redis (recomendado)"
    echo "  stop                  Para os containers"
    echo "  restart               Reinicia os containers"
    echo "  logs                  Mostra logs do container"
    echo "  status                Mostra status dos containers"
    echo "  clean                 Remove containers e imagens"
    echo "  test                  Testa a API"
    echo "  help                  Mostra esta ajuda"
    echo ""
    echo "OPÇÕES:"
    echo "  --tag TAG             Tag da imagem (padrão: latest)"
    echo "  --port PORT           Porta do host (padrão: 5000)"
    echo "  --logs-dir DIR        Diretório para logs (padrão: /opt/tripleplay-sentinel/logs)"
    echo ""
    echo "EXEMPLOS:"
    echo "  $0 build --tag v2.1.0"
    echo "  $0 run-with-redis --port 8080"
    echo "  $0 logs"
    echo "  $0 test"
}

# Função para log colorido
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Função para verificar se Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker não está instalado!"
        exit 1
    fi
}

# Função para build da imagem
build_image() {
    log "🏗️ Construindo imagem Docker..."
    
    if [ ! -f "src/collector/Dockerfile" ]; then
        log_error "Dockerfile não encontrado em src/collector/"
        exit 1
    fi
    
    cd src/collector
    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
    cd - > /dev/null
    
    log "✅ Imagem construída: ${IMAGE_NAME}:${IMAGE_TAG}"
}

# Função para criar rede Docker
create_network() {
    if ! docker network ls | grep -q "${NETWORK_NAME}"; then
        log "🌐 Criando rede Docker: ${NETWORK_NAME}"
        docker network create "${NETWORK_NAME}"
    else
        log "🌐 Rede ${NETWORK_NAME} já existe"
    fi
}

# Função para executar Redis
run_redis() {
    if docker ps | grep -q "${REDIS_CONTAINER_NAME}"; then
        log "🔴 Redis já está executando"
    else
        log "🔴 Iniciando Redis..."
        docker run -d \
            --name "${REDIS_CONTAINER_NAME}" \
            --network "${NETWORK_NAME}" \
            --restart unless-stopped \
            -p 6379:6379 \
            redis:7-alpine
        
        # Aguardar Redis inicializar
        sleep 3
        log "✅ Redis iniciado"
    fi
}

# Função para executar container standalone
run_standalone() {
    log "🚀 Executando TriplePlay-Sentinel (standalone)..."
    
    # Parar container se já estiver executando
    if docker ps | grep -q "${CONTAINER_NAME}"; then
        log_warn "Container já está executando. Parando primeiro..."
        docker stop "${CONTAINER_NAME}" > /dev/null
        docker rm "${CONTAINER_NAME}" > /dev/null
    fi
    
    docker run -d \
        --name "${CONTAINER_NAME}" \
        --restart unless-stopped \
        -p "${PORT}:5000" \
        -e COLLECTOR_HOST=0.0.0.0 \
        -e COLLECTOR_PORT=5000 \
        -e LOG_LEVEL=INFO \
        "${IMAGE_NAME}:${IMAGE_TAG}"
    
    log "✅ Container iniciado em http://localhost:${PORT}"
}

# Função para executar com Redis
run_with_redis() {
    create_network
    run_redis
    
    log "🚀 Executando TriplePlay-Sentinel com Redis..."
    
    # Criar diretório de logs
    if [ ! -d "${LOGS_DIR}" ]; then
        log "📁 Criando diretório de logs: ${LOGS_DIR}"
        sudo mkdir -p "${LOGS_DIR}"
        sudo chown -R $(id -u):$(id -g) "${LOGS_DIR}"
    fi
    
    # Parar container se já estiver executando
    if docker ps | grep -q "${CONTAINER_NAME}"; then
        log_warn "Container já está executando. Parando primeiro..."
        docker stop "${CONTAINER_NAME}" > /dev/null
        docker rm "${CONTAINER_NAME}" > /dev/null
    fi
    
    docker run -d \
        --name "${CONTAINER_NAME}" \
        --network "${NETWORK_NAME}" \
        --restart unless-stopped \
        -p "${PORT}:5000" \
        -v "${LOGS_DIR}:/app/logs" \
        -e COLLECTOR_HOST=0.0.0.0 \
        -e COLLECTOR_PORT=5000 \
        -e LOG_LEVEL=INFO \
        -e REDIS_ENABLED=true \
        -e REDIS_HOST="${REDIS_CONTAINER_NAME}" \
        -e REDIS_PORT=6379 \
        -e REDIS_DB=0 \
        -e CACHE_TTL=30 \
        -e SSH_TIMEOUT=30 \
        -e SSH_MAX_RETRIES=3 \
        -e MAX_WORKERS=10 \
        -e REQUEST_TIMEOUT=60 \
        "${IMAGE_NAME}:${IMAGE_TAG}"
    
    log "✅ Container iniciado com Redis em http://localhost:${PORT}"
}

# Função para parar containers
stop_containers() {
    log "🛑 Parando containers..."
    
    if docker ps | grep -q "${CONTAINER_NAME}"; then
        docker stop "${CONTAINER_NAME}"
        log "✅ ${CONTAINER_NAME} parado"
    fi
    
    if docker ps | grep -q "${REDIS_CONTAINER_NAME}"; then
        docker stop "${REDIS_CONTAINER_NAME}"
        log "✅ ${REDIS_CONTAINER_NAME} parado"
    fi
}

# Função para reiniciar containers
restart_containers() {
    log "🔄 Reiniciando containers..."
    
    if docker ps -a | grep -q "${CONTAINER_NAME}"; then
        docker restart "${CONTAINER_NAME}"
        log "✅ ${CONTAINER_NAME} reiniciado"
    fi
    
    if docker ps -a | grep -q "${REDIS_CONTAINER_NAME}"; then
        docker restart "${REDIS_CONTAINER_NAME}"
        log "✅ ${REDIS_CONTAINER_NAME} reiniciado"
    fi
}

# Função para mostrar logs
show_logs() {
    if docker ps | grep -q "${CONTAINER_NAME}"; then
        log "📝 Logs do ${CONTAINER_NAME}:"
        docker logs -f "${CONTAINER_NAME}"
    else
        log_error "Container ${CONTAINER_NAME} não está executando"
    fi
}

# Função para mostrar status
show_status() {
    log "📊 Status dos containers:"
    echo ""
    
    # TriplePlay-Sentinel
    if docker ps | grep -q "${CONTAINER_NAME}"; then
        echo -e "${GREEN}✅ ${CONTAINER_NAME}: EXECUTANDO${NC}"
        echo "   - Porta: ${PORT}"
        echo "   - URL: http://localhost:${PORT}"
    else
        echo -e "${RED}❌ ${CONTAINER_NAME}: PARADO${NC}"
    fi
    
    # Redis
    if docker ps | grep -q "${REDIS_CONTAINER_NAME}"; then
        echo -e "${GREEN}✅ ${REDIS_CONTAINER_NAME}: EXECUTANDO${NC}"
        echo "   - Porta: 6379"
    else
        echo -e "${RED}❌ ${REDIS_CONTAINER_NAME}: PARADO${NC}"
    fi
    
    # Imagens
    echo ""
    log "🖼️ Imagens disponíveis:"
    docker images | grep tripleplay-sentinel || echo "   Nenhuma imagem encontrada"
}

# Função para limpeza
clean_all() {
    log_warn "🧹 Limpando containers e imagens..."
    
    # Parar containers
    stop_containers
    
    # Remover containers
    if docker ps -a | grep -q "${CONTAINER_NAME}"; then
        docker rm "${CONTAINER_NAME}"
        log "🗑️ Container ${CONTAINER_NAME} removido"
    fi
    
    if docker ps -a | grep -q "${REDIS_CONTAINER_NAME}"; then
        docker rm "${REDIS_CONTAINER_NAME}"
        log "🗑️ Container ${REDIS_CONTAINER_NAME} removido"
    fi
    
    # Remover imagens
    if docker images | grep -q "${IMAGE_NAME}"; then
        docker rmi "${IMAGE_NAME}:${IMAGE_TAG}"
        log "🗑️ Imagem ${IMAGE_NAME}:${IMAGE_TAG} removida"
    fi
    
    # Remover rede
    if docker network ls | grep -q "${NETWORK_NAME}"; then
        docker network rm "${NETWORK_NAME}"
        log "🗑️ Rede ${NETWORK_NAME} removida"
    fi
    
    log "✅ Limpeza concluída"
}

# Função para testar API
test_api() {
    if ! docker ps | grep -q "${CONTAINER_NAME}"; then
        log_error "Container não está executando. Execute primeiro: $0 run-with-redis"
        exit 1
    fi
    
    log "🧪 Testando API..."
    
    # Aguardar container inicializar
    sleep 3
    
    # Teste de health
    echo -n "   Health check: "
    if curl -s "http://localhost:${PORT}/health" > /dev/null; then
        echo -e "${GREEN}✅ OK${NC}"
    else
        echo -e "${RED}❌ FALHOU${NC}"
    fi
    
    # Teste de status
    echo -n "   Status check: "
    if curl -s "http://localhost:${PORT}/status" > /dev/null; then
        echo -e "${GREEN}✅ OK${NC}"
    else
        echo -e "${RED}❌ FALHOU${NC}"
    fi
    
    echo ""
    log "🌐 Dashboard disponível em: http://localhost:${PORT}"
}

# Processar argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --logs-dir)
            LOGS_DIR="$2"
            shift 2
            ;;
        build|run|run-with-redis|stop|restart|logs|status|clean|test|help)
            COMMAND="$1"
            shift
            ;;
        *)
            log_error "Opção desconhecida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Executar comando
check_docker

case "${COMMAND:-help}" in
    build)
        build_image
        ;;
    run)
        run_standalone
        ;;
    run-with-redis)
        run_with_redis
        ;;
    stop)
        stop_containers
        ;;
    restart)
        restart_containers
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    clean)
        clean_all
        ;;
    test)
        test_api
        ;;
    help|*)
        show_help
        ;;
esac
