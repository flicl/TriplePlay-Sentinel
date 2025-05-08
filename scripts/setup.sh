#!/bin/bash

# Script para configuração inicial do ambiente de desenvolvimento do Sentinel

set -e

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Iniciando configuração do ambiente Sentinel...${NC}"

# Verifica pré-requisitos
echo -e "${YELLOW}Verificando pré-requisitos...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 não encontrado! Por favor, instale o Python 3.9 ou superior.${NC}"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}pip3 não encontrado! Por favor, instale o pip3.${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker não encontrado! Algumas funcionalidades exigem o Docker instalado.${NC}"
    echo -e "${YELLOW}Continuar mesmo assim? (S/n)${NC}"
    read -r continuar
    if [[ "$continuar" == "n" || "$continuar" == "N" ]]; then
        exit 1
    fi
fi

# Cria ambiente virtual Python se não existir
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Criando ambiente virtual Python...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Ambiente virtual criado com sucesso!${NC}"
fi

# Ativa o ambiente virtual
echo -e "${YELLOW}Ativando ambiente virtual...${NC}"
source venv/bin/activate

# Instala as dependências
echo -e "${YELLOW}Instalando dependências...${NC}"
pip install -r requirements.txt

# Cria arquivo .env para o collector se não existir
if [ ! -f "src/collector/.env" ]; then
    echo -e "${YELLOW}Criando arquivo de configuração .env...${NC}"
    cp src/collector/.env.example src/collector/.env
    echo -e "${GREEN}Arquivo .env criado. Edite-o conforme necessário.${NC}"
fi

# Cria diretório de logs se não existir
if [ ! -d "logs" ]; then
    echo -e "${YELLOW}Criando diretório de logs...${NC}"
    mkdir -p logs
fi

echo -e "${GREEN}Ambiente configurado com sucesso!${NC}"
echo -e "${YELLOW}Para executar o collector localmente:${NC}"
echo -e "  cd src/collector"
echo -e "  python collector.py"
echo
echo -e "${YELLOW}Para executar com Docker:${NC}"
echo -e "  docker-compose up -d"
echo
echo -e "${YELLOW}Para testar a conexão:${NC}"
echo -e "  curl -X GET http://localhost:5000/health"
echo 
echo -e "${GREEN}Configuração concluída!${NC}"
