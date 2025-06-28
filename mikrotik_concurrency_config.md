# Configurações MikroTik para Alta Concorrência

## 1. Aumentar Limite de Sessões SSH
```routeros
# Permite até 10 sessões SSH simultâneas
/ip service set ssh max-sessions=10

# Aumenta timeout de sessão
/ip service set ssh timeout=none
```

## 2. Otimizações de Performance
```routeros
# Configurar recursos do sistema
/system resource set max-processes=100
/system resource set max-threads=200

# Ajustar prioridades de CPU para SSH
/system scheduler add name=ssh-priority on-event="/interface print" \
    policy=read,write start-time=startup interval=1d
```

## 3. Monitoramento de Carga
```routeros
# Script para monitorar carga SSH
:local sshCount [/ip service get ssh max-sessions]
:local currentSessions [/ip service get ssh current-sessions]
:put "SSH Sessions: $currentSessions / $sshCount"

# Alerta se muitas conexões
:if ($currentSessions > 8) do={
    :log warning "Muitas sessões SSH ativas: $currentSessions"
}
```

## 4. Configuração de Rede
```routeros
# Otimizar interface para baixa latência
/interface ethernet set [find] auto-negotiation=no speed=1Gbps duplex=full

# Configurar QoS para SSH (prioridade alta)
/queue simple add name=ssh-priority target=:22/tcp priority=1/1 max-limit=10M/10M
```

## 5. Limites Recomendados
- **SSH Sessions**: 5-10 simultâneas
- **CPU Usage**: Manter < 70% 
- **Memory Usage**: Manter < 80%
- **Command Timeout**: 30-60 segundos
