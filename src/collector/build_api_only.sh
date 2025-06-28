#!/bin/bash
"""
Build Script para TriplePlay-Sentinel API-Only
Constrói e executa a versão otimizada sem SSH
"""

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
IMAGE_NAME="tripleplay-sentinel-api-only"
IMAGE_TAG="2.0.0"
CONTAINER_NAME="sentinel-api-collector"

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}  TriplePlay-Sentinel API-Only Build Script  ${NC}"
echo -e "${BLUE}===============================================${NC}"

# Função para imprimir status
print_status() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING:${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR:${NC} $1"
}

# Verifica se Docker está instalado
if ! command -v docker &> /dev/null; then
    print_error "Docker não encontrado! Instale o Docker primeiro."
    exit 1
fi

# Verifica se estamos no diretório correto
if [ ! -f "Dockerfile.api-only" ]; then
    print_error "Arquivo Dockerfile.api-only não encontrado!"
    print_error "Execute este script a partir do diretório src/collector/"
    exit 1
fi

# Para container existente se estiver rodando
if docker ps -q -f name=$CONTAINER_NAME > /dev/null; then
    print_warning "Parando container existente..."
    docker stop $CONTAINER_NAME
fi

# Remove container existente
if docker ps -aq -f name=$CONTAINER_NAME > /dev/null; then
    print_warning "Removendo container existente..."
    docker rm $CONTAINER_NAME
fi

# Remove imagem antiga se existir
if docker images -q $IMAGE_NAME:$IMAGE_TAG > /dev/null; then
    print_warning "Removendo imagem antiga..."
    docker rmi $IMAGE_NAME:$IMAGE_TAG
fi

print_status "Construindo imagem API-Only..."
docker build \
    -f Dockerfile.api-only \
    -t $IMAGE_NAME:$IMAGE_TAG \
    --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    --build-arg VERSION=$IMAGE_TAG \
    .

if [ $? -eq 0 ]; then
    print_status "✅ Imagem construída com sucesso!"
else
    print_error "❌ Falha na construção da imagem!"
    exit 1
fi

# Mostra informações da imagem
print_status "Informações da imagem:"
docker images $IMAGE_NAME:$IMAGE_TAG

# Pergunta se quer executar
echo
read -p "Deseja executar o container agora? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Iniciando container..."
    
    docker run -d \
        --name $CONTAINER_NAME \
        --restart unless-stopped \
        -p 5000:5000 \
        -e COLLECTOR_HOST=0.0.0.0 \
        -e COLLECTOR_PORT=5000 \
        -e LOG_LEVEL=INFO \
        --health-cmd="python -c \"import requests; requests.get('http://localhost:5000/health', timeout=5)\"" \
        --health-interval=30s \
        --health-timeout=10s \
        --health-start-period=10s \
        --health-retries=3 \
        $IMAGE_NAME:$IMAGE_TAG

    if [ $? -eq 0 ]; then
        print_status "✅ Container iniciado com sucesso!"
        print_status "API disponível em: http://localhost:5000"
        print_status "Dashboard em: http://localhost:5000/dashboard"
        print_status "Health check: http://localhost:5000/health"
        print_status "Stats: http://localhost:5000/api/v2/stats"
        
        echo
        print_status "Logs do container:"
        docker logs -f $CONTAINER_NAME
    else
        print_error "❌ Falha ao iniciar container!"
        exit 1
    fi
else
    print_status "Container não iniciado."
    print_status "Para executar manualmente:"
    echo -e "${BLUE}docker run -d --name $CONTAINER_NAME -p 5000:5000 $IMAGE_NAME:$IMAGE_TAG${NC}"
fi

print_status "Script concluído!"

# Informações adicionais
echo
echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}  Comandos Úteis:${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "${YELLOW}Ver logs:${NC}        docker logs -f $CONTAINER_NAME"
echo -e "${YELLOW}Parar:${NC}           docker stop $CONTAINER_NAME"  
echo -e "${YELLOW}Reiniciar:${NC}       docker restart $CONTAINER_NAME"
echo -e "${YELLOW}Shell:${NC}           docker exec -it $CONTAINER_NAME bash"
echo -e "${YELLOW}Status:${NC}          docker ps | grep $CONTAINER_NAME"
echo -e "${YELLOW}Stats:${NC}           docker stats $CONTAINER_NAME"
echo
echo -e "${YELLOW}Teste rápido:${NC}     curl http://localhost:5000/health"
echo -e "${YELLOW}Exemplo de uso:${NC}   python example_api_usage.py"
