# TriplePlay-Sentinel API-Only Collector
# Dockerfile otimizado para máxima performance (sem SSH)
FROM python:3.11-slim

# Metadata
LABEL maintainer="TriplePlay-Sentinel"
LABEL version="2.1.0"
LABEL description="Sistema de Monitoramento 100% baseado na API MikroTik (sem SSH)"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=sentinel_api_server.py
ENV COLLECTOR_HOST=0.0.0.0
ENV COLLECTOR_PORT=5000

# Diretório de trabalho
WORKDIR /app

# Copia apenas os arquivos necessários (API-only)
COPY requirements.txt .
COPY .env.example .
COPY sentinel_config.py .
COPY mikrotik_connector.py .
COPY sentinel_api_server.py .
COPY models.py .
COPY processor.py .
COPY cache.py .
COPY gunicorn.conf.py .
COPY start.sh .
COPY templates/ templates/
COPY static/ static/

# Instala dependências otimizadas e utilitários de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    dnsutils \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Torna o script executável
RUN chmod +x start.sh

# Cria usuário não-root
RUN useradd --create-home --shell /bin/bash sentinel
RUN chown -R sentinel:sentinel /app
USER sentinel

# Healthcheck otimizado usando Python (requests já está instalado)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)"

# Exposição da porta
EXPOSE 5000

# Comando de inicialização - Usar Gunicorn em produção
CMD ["./start.sh", "start"]
