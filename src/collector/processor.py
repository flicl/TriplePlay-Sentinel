#!/usr/bin/env python3
"""
TriplePlay-Sentinel - Processador de Resultados de Testes
Sistema de Monitoramento Centralizado MikroTik-Zabbix via HTTP Agent (PULL)
"""

import re
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger('sentinel-processor')


class TestProcessor:
    """
    Processador especializado para normalizar e estruturar resultados dos testes de conectividade
    """
    
    @staticmethod
    def process_ping_result(raw_output: str) -> Dict[str, Any]:
        """
        Processa resultado do comando ping do MikroTik
        
        Args:
            raw_output: Saída bruta do comando ping
            
        Returns:
            Dict com estatísticas estruturadas do ping
        """
        try:
            lines = raw_output.strip().split('\n')
            
            # Procura pela linha de estatísticas finais
            stats_line = None
            for line in lines:
                if 'sent=' in line and 'received=' in line:
                    stats_line = line
                    break
            
            if not stats_line:
                # Tenta parse alternativo para diferentes formatos do MikroTik
                return TestProcessor._parse_ping_alternative(raw_output)
            
            # Parse das estatísticas
            # Formato esperado: "sent=4 received=4 packet-loss=0% min-rtt=12ms avg-rtt=13ms max-rtt=15ms"
            stats = {}
            for part in stats_line.split():
                if '=' in part:
                    key, value = part.split('=', 1)
                    stats[key] = value
            
            # Extrai valores numéricos
            packets_sent = int(stats.get('sent', 0))
            packets_received = int(stats.get('received', 0))
            
            # Calcula packet loss
            if packets_sent > 0:
                packet_loss = ((packets_sent - packets_received) / packets_sent) * 100
            else:
                packet_loss = 100.0
            
            # Extrai tempos (remove 'ms' e converte para float)
            def extract_time(value_str):
                if value_str and value_str.endswith('ms'):
                    try:
                        return float(value_str[:-2])
                    except ValueError:
                        return None
                return None
            
            min_rtt = extract_time(stats.get('min-rtt'))
            avg_rtt = extract_time(stats.get('avg-rtt'))
            max_rtt = extract_time(stats.get('max-rtt'))
            
            # Calcula jitter (aproximação simples)
            jitter = None
            if min_rtt is not None and max_rtt is not None:
                jitter = max_rtt - min_rtt
            
            # Calcula disponibilidade
            availability = (packets_received / packets_sent * 100) if packets_sent > 0 else 0
            
            return {
                'packets_sent': packets_sent,
                'packets_received': packets_received,
                'packet_loss_percent': round(packet_loss, 2),
                'availability_percent': round(availability, 2),
                'min_time_ms': min_rtt,
                'avg_time_ms': avg_rtt,
                'max_time_ms': max_rtt,
                'jitter_ms': round(jitter, 2) if jitter is not None else None,
                'status': 'reachable' if packets_received > 0 else 'unreachable',
                'raw_output': raw_output
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar resultado do ping: {str(e)}")
            return {
                'error': f'Erro no processamento: {str(e)}',
                'status': 'error',
                'raw_output': raw_output
            }
    
    @staticmethod
    def _parse_ping_alternative(raw_output: str) -> Dict[str, Any]:
        """Parse alternativo para diferentes formatos de saída do ping MikroTik"""
        try:
            lines = raw_output.strip().split('\n')
            
            # Conta linhas de resposta de ping
            responses = []
            timeouts = 0
            
            for line in lines:
                if 'timeout' in line.lower():
                    timeouts += 1
                elif 'time=' in line:
                    # Extrai tempo da resposta individual
                    time_match = re.search(r'time=(\d+(?:\.\d+)?)ms', line)
                    if time_match:
                        responses.append(float(time_match.group(1)))
            
            total_packets = len(responses) + timeouts
            received_packets = len(responses)
            
            if total_packets == 0:
                return {
                    'error': 'Formato de saída do ping não reconhecido',
                    'status': 'error',
                    'raw_output': raw_output
                }
            
            # Calcula estatísticas
            packet_loss = (timeouts / total_packets) * 100 if total_packets > 0 else 100
            availability = (received_packets / total_packets) * 100 if total_packets > 0 else 0
            
            min_time = min(responses) if responses else None
            max_time = max(responses) if responses else None
            avg_time = sum(responses) / len(responses) if responses else None
            jitter = (max_time - min_time) if min_time and max_time else None
            
            return {
                'packets_sent': total_packets,
                'packets_received': received_packets,
                'packet_loss_percent': round(packet_loss, 2),
                'availability_percent': round(availability, 2),
                'min_time_ms': round(min_time, 2) if min_time else None,
                'avg_time_ms': round(avg_time, 2) if avg_time else None,
                'max_time_ms': round(max_time, 2) if max_time else None,
                'jitter_ms': round(jitter, 2) if jitter else None,
                'status': 'reachable' if received_packets > 0 else 'unreachable',
                'raw_output': raw_output
            }
            
        except Exception as e:
            logger.error(f"Erro no parse alternativo do ping: {str(e)}")
            return {
                'error': f'Erro no processamento alternativo: {str(e)}',
                'status': 'error',
                'raw_output': raw_output
            }
    
    @staticmethod
    def process_traceroute_result(raw_output: str, target: str) -> Dict[str, Any]:
        """
        Processa resultado do comando traceroute do MikroTik
        
        Args:
            raw_output: Saída bruta do comando traceroute
            target: Alvo do traceroute
            
        Returns:
            Dict com resultado estruturado do traceroute
        """
        try:
            lines = raw_output.strip().split('\n')
            hops_dict = {}  # Use dicionário para pegar só a versão mais recente de cada hop
            
            # Parse do formato MikroTik
            # Formato: " 1 10.172.28.1                        0%    3   2.9ms     2.6     1.2     3.6"
            
            for line in lines:
                line = line.strip()
                
                # Ignora linhas vazias e cabeçalhos
                if not line or 'ADDRESS' in line or 'LOSS' in line or line.startswith('#'):
                    continue
                
                # Parse de cada linha de hop
                hop_info = TestProcessor._parse_mikrotik_traceroute_line(line)
                if hop_info and hop_info.get('hop'):
                    # Armazena apenas a versão mais recente de cada hop
                    hop_num = hop_info['hop']
                    hops_dict[hop_num] = hop_info
            
            # Converte para lista ordenada
            hops = [hops_dict[hop_num] for hop_num in sorted(hops_dict.keys())]
            
            # Analisa resultado final
            final_hop = hops[-1] if hops else None
            reached_target = False
            
            if final_hop and final_hop.get('address'):
                # Verifica se chegou ao destino
                reached_target = (target == final_hop.get('address') or 
                                final_hop.get('loss_percent', 100) < 100)
            
            return {
                'target': target,
                'hop_count': len(hops),
                'hops': hops,
                'reached_target': reached_target,
                'max_hops': len(hops),
                'status': 'success' if reached_target else 'incomplete',
                'raw_output': raw_output
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar resultado do traceroute: {str(e)}")
            return {
                'target': target,
                'error': f'Erro no processamento: {str(e)}',
                'status': 'error',
                'raw_output': raw_output
            }
    
    @staticmethod
    def _parse_mikrotik_traceroute_line(line: str) -> Dict[str, Any]:
        """Parse de uma linha do traceroute MikroTik"""
        try:
            # Formato: " 1 10.172.28.1                        0%    3   2.9ms     2.6     1.2     3.6"
            parts = line.split()
            
            if len(parts) < 2:
                return None
            
            # Extrai número do hop
            try:
                hop_num = int(parts[0])
            except ValueError:
                return None
            
            # Verifica se há endereço IP
            address = None
            if len(parts) > 1 and not parts[1].endswith('%'):
                # Verifica se é um IP válido
                ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
                if re.match(ip_pattern, parts[1]):
                    address = parts[1]
            
            # Procura por porcentagem de perda
            loss_percent = None
            sent_count = None
            for i, part in enumerate(parts):
                if part.endswith('%'):
                    try:
                        loss_percent = float(part[:-1])
                        # O próximo valor depois da % é normalmente o count
                        if i + 1 < len(parts):
                            try:
                                sent_count = int(parts[i + 1])
                            except ValueError:
                                pass
                        break
                    except ValueError:
                        continue
            
            # Extrai tempos de resposta (procura por valores com ms)
            times = []
            time_pattern = r'(\d+(?:\.\d+)?)ms'
            for part in parts:
                match = re.match(time_pattern, part)
                if match:
                    times.append(float(match.group(1)))
            
            # Se não encontrou tempos com ms, procura por valores numéricos após o count
            if not times and sent_count is not None:
                # Procura por valores numéricos depois do count
                found_count = False
                for part in parts:
                    if found_count and part.replace('.', '').isdigit():
                        times.append(float(part))
                    elif part == str(sent_count):
                        found_count = True
            
            hop_info = {
                'hop': hop_num,
                'address': address,
                'loss_percent': loss_percent if loss_percent is not None else 0.0,
                'sent_count': sent_count,
                'status': 'timeout' if not address or loss_percent == 100 else 'responded'
            }
            
            # Mapeia os tempos baseado na posição (last, avg, best, worst)
            if times:
                hop_info['times_ms'] = times
                if len(times) >= 1:
                    hop_info['last_time_ms'] = times[0]
                if len(times) >= 2:
                    hop_info['avg_time_ms'] = times[1]
                if len(times) >= 3:
                    hop_info['best_time_ms'] = times[2]
                if len(times) >= 4:
                    hop_info['worst_time_ms'] = times[3]
            
            return hop_info
            
        except Exception as e:
            logger.debug(f"Erro ao fazer parse da linha do traceroute: {str(e)}")
            return {
                'hop': 0,
                'status': 'parse_error',
                'raw_line': line
            }


# Instância global do processador
processor = TestProcessor()