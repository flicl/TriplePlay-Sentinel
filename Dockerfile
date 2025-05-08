FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copia os arquivos de requisitos primeiro para aproveitar o cache de camadas do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY src/collector /app/

# Cria arquivo .env vazio para ser substituído em tempo de execução
RUN touch .env

# Expõe a porta padrão da aplicação
EXPOSE 5000

# Define o comando de inicialização
CMD ["python", "collector.py"]
