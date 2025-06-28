// TriplePlay-Sentinel Dashboard JavaScript
// Sistema de Monitoramento Centralizado MikroTik-Zabbix via HTTP Agent (PULL)

class SentinelDashboard {
    constructor() {
        this.baseUrl = window.location.origin;
        this.testResults = [];
        this.apiKey = localStorage.getItem('sentinel-api-key') || '';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSavedApiKey();
        this.loadStats();
        this.startStatsUpdate();
    }

    setupEventListeners() {
        // Formulário de teste
        document.getElementById('test-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.runTest();
        });

        // Botão para salvar API key
        document.getElementById('save-api-key').addEventListener('click', () => {
            this.saveApiKey();
        });

        // Enter no campo da API key
        document.getElementById('api-key').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.saveApiKey();
            }
        });
    }

    loadSavedApiKey() {
        const apiKeyInput = document.getElementById('api-key');
        const alert = document.getElementById('api-key-alert');
        
        if (this.apiKey) {
            apiKeyInput.value = this.apiKey;
            // Esconde o alerta se já tem API key
            if (alert) {
                alert.style.display = 'none';
            }
        }
    }

    saveApiKey() {
        const apiKeyInput = document.getElementById('api-key');
        const saveBtn = document.getElementById('save-api-key');
        const newApiKey = apiKeyInput.value.trim();
        
        if (newApiKey) {
            this.apiKey = newApiKey;
            localStorage.setItem('sentinel-api-key', this.apiKey);
            this.showNotification('API Key salva com sucesso!', 'success');
            
            // Atualiza visual do botão
            saveBtn.className = 'btn btn-success btn-sm';
            saveBtn.innerHTML = '<i class="fas fa-check"></i>';
            setTimeout(() => {
                saveBtn.className = 'btn btn-outline-light btn-sm';
                saveBtn.innerHTML = '<i class="fas fa-save"></i>';
            }, 2000);
            
            // Recarrega as estatísticas com a nova API key
            this.loadStats();
        } else {
            this.apiKey = '';
            localStorage.removeItem('sentinel-api-key');
            this.showNotification('API Key removida', 'info');
            
            // Atualiza status para mostrar que autenticação é necessária
            this.updateStatusIndicator(false, 'Erro: Autenticação requerida');
        }
    }

    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }
        
        return headers;
    }



    async loadStats() {
        try {
            const response = await fetch(`${this.baseUrl}/api/health`, {
                headers: this.getAuthHeaders()
            });
            
            if (response.status === 401) {
                this.updateStatusIndicator(false, 'Erro: Autenticação requerida');
                this.showApiKeyAlert();
                return;
            }
            
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.updateStatusIndicator(true);
                this.updateMetrics(data);
                this.updateDetailedStats(data);
                this.hideApiKeyAlert();
            } else {
                this.updateStatusIndicator(false, 'Erro: Serviço indisponível');
            }
        } catch (error) {
            console.error('Erro ao carregar estatísticas:', error);
            this.updateStatusIndicator(false, 'Erro: Falha na conexão');
        }
    }

    showApiKeyAlert() {
        const alert = document.getElementById('api-key-alert');
        if (alert) {
            alert.style.display = 'block';
        }
    }

    hideApiKeyAlert() {
        const alert = document.getElementById('api-key-alert');
        if (alert) {
            alert.style.display = 'none';
        }
    }

    updateStatusIndicator(isOnline, customMessage = null) {
        const indicator = document.getElementById('status-indicator');
        if (isOnline) {
            indicator.className = 'badge bg-success';
            indicator.innerHTML = '<i class="fas fa-check-circle"></i> Online';
        } else {
            indicator.className = 'badge bg-danger';
            indicator.innerHTML = `<i class="fas fa-times-circle"></i> ${customMessage || 'Offline'}`;
        }
    }

    updateMetrics(data) {
        // Uptime
        const uptime = this.formatUptime(data.uptime_seconds);
        document.getElementById('uptime').textContent = uptime;

        // Requisições totais
        const totalRequests = data.requests?.total || 0;
        document.getElementById('total-requests').textContent = totalRequests.toLocaleString();

        // Cache hits
        const cacheHitRate = data.cache?.hit_rate_percent || 0;
        document.getElementById('cache-hits').textContent = `${cacheHitRate}%`;

        // Conexões API
        const apiConnections = data.connections?.active_api || 0;
        document.getElementById('api-connections').textContent = apiConnections;
    }

    updateDetailedStats(data) {
        const container = document.getElementById('detailed-stats');
        
        const html = `
            <div class="row">
                <div class="col-6">
                    <h6 class="text-muted">Cache</h6>
                    <ul class="list-unstyled">
                        <li><strong>Tamanho:</strong> ${data.cache?.size || 0}/${data.cache?.max_size || 0}</li>
                        <li><strong>TTL:</strong> ${data.cache?.ttl_seconds || 0}s</li>
                        <li><strong>Hits:</strong> ${data.cache?.hits || 0}</li>
                        <li><strong>Misses:</strong> ${data.cache?.misses || 0}</li>
                    </ul>
                </div>
                <div class="col-6">
                    <h6 class="text-muted">Conexões</h6>
                    <ul class="list-unstyled">
                        <li><strong>Ativas:</strong> ${data.connections?.active_api || 0}</li>
                        <li><strong>Total:</strong> ${data.connections?.total_connections || 0}</li>
                        <li><strong>Pool:</strong> ${data.connections?.pool_size || 0}</li>
                        <li><strong>Falhas:</strong> ${data.connections?.failed_connections || 0}</li>
                    </ul>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-12">
                    <h6 class="text-muted">Requisições</h6>
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar bg-success" style="width: ${data.requests?.success_rate_percent || 0}%">
                            ${(data.requests?.success_rate_percent || 0).toFixed(1)}% Sucesso
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }

    async runTest() {
        const btn = document.getElementById('run-test-btn');
        const originalHtml = btn.innerHTML;
        
        // Verifica se a API key está configurada
        if (!this.apiKey) {
            this.showNotification('Por favor, configure a API Key primeiro', 'warning');
            return;
        }
        
        // Atualiza botão para estado de loading
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Executando...';

        try {
            const formData = this.getFormData();
            
            const response = await fetch(`${this.baseUrl}/api/test`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(formData)
            });

            if (response.status === 401) {
                this.showNotification('Erro: API Key inválida ou expirada', 'danger');
                return;
            }

            const result = await response.json();
            
            if (response.ok) {
                this.addTestResult(result);
                this.showNotification('Teste executado com sucesso!', 'success');
            } else {
                this.showNotification(`Erro: ${result.message}`, 'danger');
            }
            
        } catch (error) {
            console.error('Erro ao executar teste:', error);
            this.showNotification('Erro de conexão ao executar teste', 'danger');
        } finally {
            // Restaura botão
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    }

    getFormData() {
        return {
            mikrotik_host: document.getElementById('mikrotik-host').value,
            mikrotik_user: document.getElementById('mikrotik-user').value,
            mikrotik_password: document.getElementById('mikrotik-password').value,
            mikrotik_port: parseInt(document.getElementById('mikrotik-port').value) || 8728,
            test_type: document.getElementById('test-type').value,
            target: document.getElementById('target').value,
            count: 4,
            size: 64,
            interval: 1
        };
    }

    addTestResult(result) {
        this.testResults.unshift(result);
        this.updateTestResultsDisplay();
    }

    updateTestResultsDisplay() {
        const container = document.getElementById('test-results');
        
        if (this.testResults.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">Nenhum teste executado ainda.</p>';
            return;
        }

        let html = '';
        this.testResults.slice(0, 10).forEach((result, index) => {
            const statusClass = result.status === 'success' ? 'success' : 'danger';
            const cacheIcon = result.cache_hit ? '<i class="fas fa-tachometer-alt text-warning" title="Cache Hit"></i>' : '';
            
            html += `
                <div class="card mb-2">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div>
                            <span class="badge bg-${statusClass}">${result.status}</span>
                            <strong>${result.test_type.toUpperCase()}</strong>
                            ${result.mikrotik_host} → ${result.target}
                            ${cacheIcon}
                        </div>
                        <small class="text-muted">${new Date(result.timestamp).toLocaleString()}</small>
                    </div>
                    <div class="card-body">
                        ${this.formatTestResults(result)}
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    formatTestResults(result) {
        if (result.status === 'error') {
            return `<div class="alert alert-danger">Erro: ${result.error_message}</div>`;
        }

        let html = '<div class="row">';
        
        // Resultados específicos por tipo de teste
        if (result.test_type === 'ping' && result.results.ping_stats) {
            const stats = result.results.ping_stats;
            html += `
                <div class="col-md-6">
                    <h6>Estatísticas de Ping</h6>
                    <ul class="list-unstyled">
                        <li><strong>Pacotes:</strong> ${stats.packets_sent}/${stats.packets_received}</li>
                        <li><strong>Perda:</strong> ${stats.packet_loss_percent}%</li>
                        <li><strong>Tempo Médio:</strong> ${stats.avg_time_ms}ms</li>
                        <li><strong>Jitter:</strong> ${stats.jitter_ms !== null && stats.jitter_ms !== undefined ? stats.jitter_ms : 'N/A'}ms</li>
                    </ul>
                </div>
            `;
        } else if (result.test_type === 'traceroute' && result.results.traceroute_stats) {
            const stats = result.results.traceroute_stats;
            html += `
                <div class="col-md-6">
                    <h6>Traceroute</h6>
                    <ul class="list-unstyled">
                        <li><strong>Hops:</strong> ${stats.hop_count}</li>
                        <li><strong>Destino:</strong> ${stats.reached_target ? 'Alcançado' : 'Não alcançado'}</li>
                        <li><strong>Status:</strong> ${stats.status}</li>
                    </ul>
                </div>
            `;
        }

        // Informações gerais
        html += `
            <div class="col-md-6">
                <h6>Informações Gerais</h6>
                <ul class="list-unstyled">
                    <li><strong>Tempo de Execução:</strong> ${result.execution_time_seconds?.toFixed(2) || 'N/A'}s</li>
                    <li><strong>Cache TTL:</strong> ${result.cache_ttl}s</li>
                    <li><strong>Timestamp:</strong> ${new Date(result.timestamp).toLocaleTimeString()}</li>
                </ul>
            </div>
        `;

        html += '</div>';

        // Saída bruta (colapsável)
        if (result.raw_output) {
            html += `
                <div class="mt-3">
                    <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="collapse" data-bs-target="#raw-output-${result.timestamp.replace(/[:.]/g, '')}" aria-expanded="false">
                        <i class="fas fa-code"></i> Ver Saída Bruta
                    </button>
                    <div class="collapse mt-2" id="raw-output-${result.timestamp.replace(/[:.]/g, '')}">
                        <pre class="test-result bg-light p-2 rounded"><code>${result.raw_output}</code></pre>
                    </div>
                </div>
            `;
        }

        return html;
    }

    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);

        if (days > 0) {
            return `${days}d ${hours}h ${minutes}m`;
        } else if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else {
            return `${minutes}m`;
        }
    }

    showNotification(message, type) {
        // Cria elemento de notificação
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alert);

        // Remove automaticamente após 5 segundos
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    startStatsUpdate() {
        // Atualiza estatísticas a cada 30 segundos
        setInterval(() => {
            this.loadStats();
        }, 30000);
    }
}

// Funções globais
function clearResults() {
    if (confirm('Tem certeza que deseja limpar todos os resultados?')) {
        window.dashboard.testResults = [];
        window.dashboard.updateTestResultsDisplay();
        window.dashboard.showNotification('Resultados limpos', 'info');
    }
}

// Inicializa dashboard quando a página carrega
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new SentinelDashboard();
});