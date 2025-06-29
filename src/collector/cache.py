#!/usr/bin/env python3
"""
TriplePlay-Sentinel - Sistema de Cache Inteligente
Sistema de Monitoramento Centralizado MikroTik-Zabbix via HTTP Agent (PULL)
"""

import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from models import TestResult, CacheEntry
from sentinel_config import config

logger = logging.getLogger('sentinel-cache')


class SentinelCache:
    """
    Sistema de cache inteligente com TTL automático e limpeza de entradas expiradas
    """
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'cleanups': 0
        }
    
    def get(self, mikrotik_host: str, test_type: str, target: str, **kwargs) -> Optional[TestResult]:
        """
        Recupera resultado do cache se ainda válido
        
        Args:
            mikrotik_host: Host do MikroTik
            test_type: Tipo do teste (ping, tcp, traceroute)
            target: Alvo do teste
            **kwargs: Parâmetros adicionais do teste
            
        Returns:
            TestResult se encontrado e válido, None caso contrário
        """
        cache_key = self._generate_cache_key(mikrotik_host, test_type, target, **kwargs)
        
        with self._lock:
            entry = self._cache.get(cache_key)
            
            if entry is None:
                self._stats['misses'] += 1
                logger.debug(f"Cache MISS para chave: {cache_key}")
                return None
            
            if entry.is_expired():
                # Remove entrada expirada
                del self._cache[cache_key]
                del self._timestamps[cache_key]
                self._stats['misses'] += 1
                self._stats['evictions'] += 1
                logger.debug(f"Cache EXPIRADO para chave: {cache_key}")
                return None
            
            # Cache hit válido
            self._stats['hits'] += 1
            logger.debug(f"Cache HIT para chave: {cache_key}")
            
            # Marca como cache hit
            result = entry.result
            result.cache_hit = True
            return result
    
    def set(self, mikrotik_host: str, test_type: str, target: str, result: TestResult, **kwargs):
        """
        Armazena resultado no cache
        
        Args:
            mikrotik_host: Host do MikroTik
            test_type: Tipo do teste
            target: Alvo do teste
            result: Resultado do teste para armazenar
            **kwargs: Parâmetros adicionais do teste
        """
        cache_key = self._generate_cache_key(mikrotik_host, test_type, target, **kwargs)
        expiry = datetime.now() + timedelta(seconds=config.CACHE_TTL)
        
        with self._lock:
            # Verifica se precisa fazer limpeza por tamanho
            if len(self._cache) >= config.MAX_CACHE_SIZE:
                self._cleanup_oldest_entries()
            
            # Armazena entrada
            self._cache[cache_key] = CacheEntry(result=result, expiry=expiry)
            self._timestamps[cache_key] = datetime.now()
            
            logger.debug(f"Resultado armazenado no cache: {cache_key}")
    
    def clear(self) -> int:
        """
        Limpa todo o cache
        
        Returns:
            Número de entradas removidas
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._timestamps.clear()
            logger.info(f"Cache limpo: {count} entradas removidas")
            return count
    
    def cleanup_expired(self) -> int:
        """
        Remove entradas expiradas do cache
        
        Returns:
            Número de entradas removidas
        """
        with self._lock:
            expired_keys = []
            now = datetime.now()
            
            for key, entry in self._cache.items():
                if entry.expiry <= now:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                del self._timestamps[key]
            
            if expired_keys:
                self._stats['cleanups'] += 1
                self._stats['evictions'] += len(expired_keys)
                logger.debug(f"Limpeza automática: {len(expired_keys)} entradas expiradas removidas")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': config.MAX_CACHE_SIZE,
                'ttl_seconds': config.CACHE_TTL,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate_percent': round(hit_rate, 2),
                'evictions': self._stats['evictions'],
                'cleanups': self._stats['cleanups']
            }
    
    def get_entries_info(self) -> List[Dict]:
        """Retorna informações detalhadas das entradas do cache"""
        with self._lock:
            entries = []
            now = datetime.now()
            
            for key, entry in self._cache.items():
                age = (now - self._timestamps.get(key, now)).total_seconds()
                expires_in = (entry.expiry - now).total_seconds()
                
                entries.append({
                    'key': key,
                    'test_type': entry.result.test_type,
                    'mikrotik_host': entry.result.mikrotik_host,
                    'target': entry.result.target,
                    'age_seconds': round(age, 2),
                    'expires_in_seconds': max(0, round(expires_in, 2)),
                    'timestamp': entry.result.timestamp
                })
            
            return sorted(entries, key=lambda x: x['age_seconds'], reverse=True)
    
    def _generate_cache_key(self, mikrotik_host: str, test_type: str, target: str, **kwargs) -> str:
        """Gera chave única para o cache"""
        import hashlib
        import json
        
        key_data = {
            'host': mikrotik_host,
            'type': test_type,
            'target': target,
            **kwargs
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _cleanup_oldest_entries(self):
        """Remove as entradas mais antigas quando cache atinge tamanho máximo"""
        # Remove 20% das entradas mais antigas
        entries_to_remove = max(1, len(self._cache) // 5)
        
        # Ordena por timestamp (mais antigo primeiro)
        sorted_entries = sorted(
            self._timestamps.items(),
            key=lambda x: x[1]
        )
        
        for key, _ in sorted_entries[:entries_to_remove]:
            if key in self._cache:
                del self._cache[key]
            if key in self._timestamps:
                del self._timestamps[key]
        
        self._stats['evictions'] += entries_to_remove
        logger.debug(f"Limpeza por tamanho: {entries_to_remove} entradas antigas removidas")


# Instância global do cache
cache = SentinelCache()