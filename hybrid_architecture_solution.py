# Solução Definitiva: Arquitetura Híbrida para Alta Concorrência

## 🎯 Abordagem em Camadas

### Camada 1: Request Aggregation
```python
class RequestAggregator:
    """Agrupa requests similares para otimizar execução"""
    
    def __init__(self):
        self.pending_requests = {}
        self.aggregation_window = 2  # 2 segundos para agrupar
    
    def add_request(self, mikrotik_host, targets, callback):
        """Adiciona request ao agregador"""
        
        key = mikrotik_host
        if key not in self.pending_requests:
            self.pending_requests[key] = {
                'targets': set(),
                'callbacks': [],
                'timer': None
            }
        
        # Adiciona targets e callback
        self.pending_requests[key]['targets'].update(targets)
        self.pending_requests[key]['callbacks'].append(callback)
        
        # Agenda execução se primeira request
        if not self.pending_requests[key]['timer']:
            timer = threading.Timer(self.aggregation_window, 
                                  self._execute_aggregated, [key])
            timer.start()
            self.pending_requests[key]['timer'] = timer
    
    def _execute_aggregated(self, mikrotik_host):
        """Executa requests agregadas"""
        
        if mikrotik_host in self.pending_requests:
            request_info = self.pending_requests.pop(mikrotik_host)
            
            # Executa batch para todos os targets
            results = execute_batch_ping(
                mikrotik_host, 
                list(request_info['targets'])
            )
            
            # Notifica todos os callbacks
            for callback in request_info['callbacks']:
                callback(results)
```

### Camada 2: Smart Load Balancing
```python
class SmartLoadBalancer:
    """Load balancer consciente da carga do MikroTik"""
    
    def __init__(self):
        self.mikrotik_load = {}  # host -> carga atual
        self.max_concurrent = {}  # host -> limite máximo
    
    def can_accept_request(self, mikrotik_host) -> bool:
        """Verifica se MikroTik pode aceitar mais requests"""
        
        current_load = self.mikrotik_load.get(mikrotik_host, 0)
        max_load = self.max_concurrent.get(mikrotik_host, 5)
        
        return current_load < max_load
    
    def queue_request(self, mikrotik_host, request):
        """Enfileira request se necessário"""
        
        if self.can_accept_request(mikrotik_host):
            # Executa imediatamente
            self._execute_immediate(mikrotik_host, request)
        else:
            # Enfileira para execução posterior
            self._add_to_queue(mikrotik_host, request)
    
    def _execute_immediate(self, mikrotik_host, request):
        """Executa request imediatamente"""
        
        # Incrementa carga
        self.mikrotik_load[mikrotik_host] = \
            self.mikrotik_load.get(mikrotik_host, 0) + 1
        
        try:
            # Executa request
            result = execute_request(mikrotik_host, request)
            return result
        finally:
            # Decrementa carga
            self.mikrotik_load[mikrotik_host] -= 1
            
            # Processa próximo da fila
            self._process_queue(mikrotik_host)
```

### Camada 3: Circuit Breaker
```python
class CircuitBreaker:
    """Protege MikroTik de sobrecarga"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = {}
        self.last_failure_time = {}
        self.state = {}  # 'closed', 'open', 'half-open'
    
    def can_execute(self, mikrotik_host) -> bool:
        """Verifica se pode executar no MikroTik"""
        
        state = self.state.get(mikrotik_host, 'closed')
        
        if state == 'closed':
            return True
        elif state == 'open':
            # Verifica se pode tentar recovery
            last_failure = self.last_failure_time.get(mikrotik_host, 0)
            if time.time() - last_failure > self.recovery_timeout:
                self.state[mikrotik_host] = 'half-open'
                return True
            return False
        elif state == 'half-open':
            return True
    
    def record_success(self, mikrotik_host):
        """Registra sucesso"""
        self.failure_count[mikrotik_host] = 0
        self.state[mikrotik_host] = 'closed'
    
    def record_failure(self, mikrotik_host):
        """Registra falha"""
        self.failure_count[mikrotik_host] = \
            self.failure_count.get(mikrotik_host, 0) + 1
        
        if self.failure_count[mikrotik_host] >= self.failure_threshold:
            self.state[mikrotik_host] = 'open'
            self.last_failure_time[mikrotik_host] = time.time()
```

## 🎯 Arquitetura Final Integrada

```python
@app.route('/api/test', methods=['POST'])
@require_auth  
def execute_test_optimized():
    """Endpoint otimizado para alta concorrência"""
    
    try:
        params = parse_request_params(request.get_json())
        
        # 1. Verifica circuit breaker
        if not circuit_breaker.can_execute(params.mikrotik_host):
            return jsonify({
                'status': 'error',
                'message': 'MikroTik temporariamente indisponível (circuit breaker)'
            }), 503
        
        # 2. Verifica cache primeiro
        cached_result = cache.get(cache_key)
        if cached_result:
            return jsonify(cached_result.to_dict())
        
        # 3. Verifica load balancer
        if not load_balancer.can_accept_request(params.mikrotik_host):
            # Retorna erro de sobrecarga
            return jsonify({
                'status': 'error', 
                'message': 'MikroTik sobrecarregado, tente novamente',
                'retry_after': 5
            }), 429
        
        # 4. Adiciona ao agregador para execução otimizada
        future = request_aggregator.add_request(
            params.mikrotik_host,
            [params.target],
            params
        )
        
        # 5. Aguarda resultado
        result = future.result(timeout=60)
        
        # 6. Registra sucesso no circuit breaker
        circuit_breaker.record_success(params.mikrotik_host)
        
        return jsonify(result.to_dict())
        
    except Exception as e:
        # Registra falha no circuit breaker
        circuit_breaker.record_failure(params.mikrotik_host)
        
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

## 📊 Performance Final Esperada

| Cenário | Requests/s | MikroTik Load | Latência |
|---------|------------|---------------|----------|
| **10 requests** | 10/s | 30% CPU | 200ms |
| **50 requests** | 25/s | 60% CPU | 400ms |
| **100 requests** | 35/s | 80% CPU | 800ms |
| **200+ requests** | Circuit breaker ativo | - | 503 Error |

**🎯 Resultado**: Sistema protegido, performance otimizada e MikroTik preservado!
