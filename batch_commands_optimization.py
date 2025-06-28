#!/usr/bin/env python3
"""
Implementação de comandos batch para otimizar múltiplos pings no mesmo MikroTik
"""

def create_batch_ping_command(targets: list, count: int = 4) -> str:
    """
    Cria comando batch para executar múltiplos pings em uma única sessão SSH
    
    Args:
        targets: Lista de IPs para ping
        count: Número de pings por target
    
    Returns:
        Comando MikroTik batch
    """
    
    commands = []
    for i, target in enumerate(targets):
        # Cada ping com identificador único
        cmd = f'/ping {target} count={count} comment="ping_{i}_{target}"'
        commands.append(cmd)
    
    # Comando batch MikroTik
    batch_command = '; '.join(commands)
    
    return batch_command


def parse_batch_ping_results(output: str, targets: list) -> dict:
    """
    Parse dos resultados de batch ping
    
    Args:
        output: Output bruto do comando batch
        targets: Lista de targets originais
    
    Returns:
        Dict com resultados separados por target
    """
    
    results = {}
    lines = output.split('\n')
    
    current_target = None
    current_lines = []
    
    for line in lines:
        # Detecta início de novo ping baseado no comment
        for i, target in enumerate(targets):
            if f'ping_{i}_{target}' in line:
                # Salva resultado anterior se existir
                if current_target and current_lines:
                    results[current_target] = '\n'.join(current_lines)
                
                # Inicia novo target
                current_target = target
                current_lines = [line]
                break
        else:
            # Linha pertence ao target atual
            if current_target:
                current_lines.append(line)
    
    # Salva último resultado
    if current_target and current_lines:
        results[current_target] = '\n'.join(current_lines)
    
    return results


# Exemplo de uso otimizado
def optimized_multi_ping(mikrotik_host: str, targets: list) -> dict:
    """
    Executa múltiplos pings de forma otimizada usando batch command
    
    Args:
        mikrotik_host: IP do MikroTik
        targets: Lista de targets para ping
    
    Returns:
        Dict com resultados por target
    """
    
    # 1. Cria comando batch
    batch_cmd = create_batch_ping_command(targets, count=4)
    
    # 2. Executa UMA vez no MikroTik (em vez de N vezes)
    ssh_result = mikrotik_connector.execute_command(
        mikrotik_host, 'admin', 'password', batch_cmd
    )
    
    # 3. Parse dos resultados separados
    if ssh_result['status'] == 'success':
        parsed_results = parse_batch_ping_results(ssh_result['output'], targets)
        
        # 4. Processa cada resultado individualmente
        final_results = {}
        for target, raw_output in parsed_results.items():
            final_results[target] = processor.process_ping_result(raw_output)
        
        return final_results
    
    else:
        return {'error': ssh_result['error']}


# Performance comparison:
"""
MÉTODO ATUAL (5 targets, 1 conexão):
- 5 comandos SSH sequenciais
- Tempo: 5 × 2s = 10 segundos

MÉTODO BATCH (5 targets, 1 conexão):
- 1 comando SSH batch
- Tempo: ~6 segundos (ping paralelo no MikroTik)

MÉTODO MÚLTIPLAS CONEXÕES (5 targets, 5 conexões):
- 5 comandos SSH paralelos  
- Tempo: ~2 segundos

MÉTODO HÍBRIDO (Batch + Múltiplas conexões):
- Para 20 targets: 4 comandos batch × 5 conexões
- Tempo: ~3 segundos para 20 targets
"""
