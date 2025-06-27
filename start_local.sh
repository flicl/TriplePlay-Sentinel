#!/bin/bash

# TriplePlay-Sentinel - Script de Inicialização Local
# Sistema de Monitoramento Centralizado MikroTik-Zabbix via HTTP Agent (PULL)

echo "============================================================"
echo "🛡️  TriplePlay-Sentinel - Inicialização Local"
echo "============================================================"

# Navega para o diretório do collector
cd "$(dirname "$0")/src/collector" || exit 1

# Verifica se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual Python..."
    python3 -m venv venv
fi

# Ativa o ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Instala/atualiza dependências
echo "📋 Instalando/atualizando dependências..."
pip install -q -r requirements.txt

# Cria diretório de logs se não existir
mkdir -p logs

# Mata processos existentes
echo "🧹 Limpando processos existentes..."
pkill -f "python app.py" 2>/dev/null || true

# Inicia o servidor
echo "🚀 Iniciando TriplePlay-Sentinel Collector..."
echo "   - URL: http://localhost:5000"
echo "   - Health: http://localhost:5000/api/health"
echo "   - Dashboard: http://localhost:5000/dashboard"
echo ""
echo "   Pressione Ctrl+C para parar o servidor"
echo "============================================================"

# Executa o servidor em foreground
python app.py