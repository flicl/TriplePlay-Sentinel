#!/bin/bash

# TriplePlay-Sentinel - Script de Testes Rápidos
# Sistema de Monitoramento Centralizado MikroTik-Zabbix via HTTP Agent (PULL)

COLLECTOR_URL="http://localhost:5000"
MIKROTIK_HOST="172.16.255.1"
MIKROTIK_USER="teste-sentinel"
MIKROTIK_PASSWORD="152436"
MIKROTIK_PORT="38222"

echo "============================================================"
echo "🧪 TriplePlay-Sentinel - Testes Rápidos"
echo "============================================================"

# Função para testar endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    
    echo "📡 Testando: $name"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$COLLECTOR_URL$endpoint")
    else
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$COLLECTOR_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]*$//')
    
    if [ "$http_code" = "200" ]; then
        echo "   ✅ Status: $http_code"
        if command -v jq &> /dev/null; then
            echo "$body" | jq . 2>/dev/null || echo "   📄 Resposta: $body"
        else
            echo "   📄 Resposta: $body"
        fi
    else
        echo "   ❌ Status: $http_code"
        echo "   📄 Resposta: $body"
    fi
    echo ""
}

# Testa se o collector está rodando
echo "1. Verificando se o collector está ativo..."
if ! curl -s "$COLLECTOR_URL/api/health" > /dev/null; then
    echo "   ❌ Collector não está rodando!"
    echo "   💡 Execute: ./start_local.sh"
    exit 1
fi
echo "   ✅ Collector está ativo!"
echo ""

# Executa testes
test_endpoint "Health Check" "GET" "/api/health" ""

test_endpoint "Teste de Conexão SSH" "POST" "/api/connection-test" '{
    "mikrotik_host": "'$MIKROTIK_HOST'",
    "mikrotik_user": "'$MIKROTIK_USER'",
    "mikrotik_password": "'$MIKROTIK_PASSWORD'",
    "mikrotik_port": '$MIKROTIK_PORT'
}'

test_endpoint "Teste de Ping" "POST" "/api/test" '{
    "mikrotik_host": "'$MIKROTIK_HOST'",
    "mikrotik_user": "'$MIKROTIK_USER'",
    "mikrotik_password": "'$MIKROTIK_PASSWORD'",
    "mikrotik_port": '$MIKROTIK_PORT',
    "target": "8.8.8.8",
    "test_type": "ping",
    "count": 3
}'

test_endpoint "Teste de Traceroute" "POST" "/api/test" '{
    "mikrotik_host": "'$MIKROTIK_HOST'",
    "mikrotik_user": "'$MIKROTIK_USER'",
    "mikrotik_password": "'$MIKROTIK_PASSWORD'",
    "mikrotik_port": '$MIKROTIK_PORT',
    "target": "8.8.8.8",
    "test_type": "traceroute"
}'

echo "============================================================"
echo "✅ Testes concluídos!"
echo "============================================================"