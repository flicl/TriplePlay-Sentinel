#!/bin/bash
# Script para testar o Sentinel Collector

function show_help {
    echo "Sentinel Collector - Script de teste"
    echo ""
    echo "Uso: $0 [opções]"
    echo ""
    echo "Opções:"
    echo "  -m, --mikrotik HOSTNAME    Endereço IP/Hostname do MikroTik"
    echo "  -u, --user USERNAME        Nome de usuário para MikroTik"
    echo "  -p, --password PASSWORD    Senha para MikroTik"
    echo "  -t, --target IP            Endereço IP alvo para teste"
    echo "  -T, --test TYPE            Tipo de teste (ping, tcp, traceroute)"
    echo "  -s, --server URL           URL do collector (padrão: http://localhost:5000)"
    echo "  -c, --count NUMBER         Número de pacotes para ping (padrão: 3)"
    echo "  -P, --port NUMBER          Porta TCP para teste TCP (padrão: 80)"
    echo "  -h, --help                 Mostra esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0 -m 192.168.1.1 -u admin -p senha -t 8.8.8.8 -T ping"
    echo "  $0 -m 192.168.1.1 -u admin -p senha -t google.com -T tcp -P 443"
    echo "  $0 -m 192.168.1.1 -u admin -p senha -t 1.1.1.1 -T traceroute"
    echo ""
}

# Valores padrão
COLLECTOR_URL="http://localhost:5000"
TEST_TYPE="ping"
COUNT=3
PORT=80

# Parse argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mikrotik)
            MIKROTIK="$2"
            shift 2
            ;;
        -u|--user)
            USERNAME="$2"
            shift 2
            ;;
        -p|--password)
            PASSWORD="$2"
            shift 2
            ;;
        -t|--target)
            TARGET="$2"
            shift 2
            ;;
        -T|--test)
            TEST_TYPE="$2"
            shift 2
            ;;
        -s|--server)
            COLLECTOR_URL="$2"
            shift 2
            ;;
        -c|--count)
            COUNT="$2"
            shift 2
            ;;
        -P|--port)
            PORT="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Opção desconhecida: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validar argumentos obrigatórios
if [ -z "$MIKROTIK" ] || [ -z "$USERNAME" ] || [ -z "$PASSWORD" ] || [ -z "$TARGET" ]; then
    echo "Erro: Argumentos obrigatórios faltando!"
    show_help
    exit 1
fi

# Prepare JSON data
if [ "$TEST_TYPE" = "ping" ]; then
    DATA="{\"mikrotik_host\":\"$MIKROTIK\",\"mikrotik_user\":\"$USERNAME\",\"mikrotik_password\":\"$PASSWORD\",\"test_type\":\"ping\",\"target\":\"$TARGET\",\"count\":$COUNT}"
elif [ "$TEST_TYPE" = "tcp" ]; then
    DATA="{\"mikrotik_host\":\"$MIKROTIK\",\"mikrotik_user\":\"$USERNAME\",\"mikrotik_password\":\"$PASSWORD\",\"test_type\":\"tcp\",\"target\":\"$TARGET\",\"port\":$PORT}"
elif [ "$TEST_TYPE" = "traceroute" ]; then
    DATA="{\"mikrotik_host\":\"$MIKROTIK\",\"mikrotik_user\":\"$USERNAME\",\"mikrotik_password\":\"$PASSWORD\",\"test_type\":\"traceroute\",\"target\":\"$TARGET\"}"
else
    echo "Erro: Tipo de teste desconhecido: $TEST_TYPE"
    exit 1
fi

echo "Executando teste $TEST_TYPE para $TARGET via $MIKROTIK..."
curl -s -X POST "$COLLECTOR_URL/api/test" \
     -H "Content-Type: application/json" \
     -d "$DATA" | jq

status=$?
if [ $status -ne 0 ]; then
    echo "Erro: Falha ao executar o teste. Verifique se o collector está em execução em $COLLECTOR_URL"
    exit 1
fi

echo "Teste concluído com sucesso!"
