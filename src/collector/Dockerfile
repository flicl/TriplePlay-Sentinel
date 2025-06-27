# Dockerfile para TriplePlay-Sentinel Collector
# Sistema de Monitoramento Centralizado MikroTik-Zabbix via HTTP Agent (PULL)

FROM python:3.11-slim

# Metadados
LABEL maintainer="TriplePlay Team <support@tripleplay.com>"
LABEL version="2.0.0"
LABEL description="TriplePlay-Sentinel Collector - Sistema de Monitoramento Centralizado MikroTik-Zabbix"

# Argumentos de build
ARG DEBIAN_FRONTEND=noninteractive

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    openssh-client \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Cria usuário não-root para segurança
RUN groupadd -r sentinel && useradd -r -g sentinel sentinel

# Diretório de trabalho
WORKDIR /app

# Copia requirements primeiro (para cache de layer)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia código fonte
COPY . .

# Cria diretórios necessários
RUN mkdir -p /app/logs && \
    chown -R sentinel:sentinel /app

# Muda para usuário não-root
USER sentinel

# Portas expostas
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Variáveis de ambiente padrão
ENV COLLECTOR_HOST=0.0.0.0
ENV COLLECTOR_PORT=5000
ENV LOG_LEVEL=INFO
ENV CACHE_TTL=30
ENV PYTHONUNBUFFERED=1

# Comando padrão
CMD ["python", "-u", "app.py"]