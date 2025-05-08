# Guia de Instalação do Sentinel

Este guia detalha os passos necessários para instalar e configurar o sistema Sentinel em seu ambiente.

## Pré-requisitos

Antes de iniciar a instalação, certifique-se de que seu sistema atende aos seguintes requisitos:

### Software
- Docker 20.10.x ou superior
- Docker Compose 2.x ou superior
- Zabbix 5.0+ (Server ou Proxy)
- Acesso a dispositivos MikroTik com API ou SSH habilitados

### Hardware
- Mínimo de 2GB de RAM para o container do collector
- 2 vCPUs ou mais recomendados
- 10GB de espaço em disco para logs e dados

## Instalação do Docker e Docker Compose

### Para Ubuntu/Debian

```bash
# Atualizar o sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Adicionar chave GPG do Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Adicionar repositório
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar instalação
docker --version
docker-compose --version
```

### Para CentOS/RHEL

```bash
# Instalar dependências
sudo yum install -y yum-utils device-mapper-persistent-data lvm2

# Adicionar repositório
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Instalar Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io

# Iniciar e habilitar Docker
sudo systemctl start docker
sudo systemctl enable docker

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Instalação do Sentinel

### 1. Clone o Repositório

```bash
git clone https://github.com/tripleplay/sentinel.git
cd sentinel
```

### 2. Configuração do Ambiente

Crie um arquivo `.env` no diretório raiz do projeto:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```
# Configuração do collector
COLLECTOR_PORT=8000
AUTH_TOKEN=seu_token_secreto_aqui
LOG_LEVEL=INFO

# Configuração TLS (opcional)
ENABLE_TLS=false
TLS_CERT_PATH=/path/to/cert.pem
TLS_KEY_PATH=/path/to/key.pem
```

### 3. Construção da Imagem Docker

```bash
docker-compose build
```

### 4. Inicialização do Serviço

```bash
docker-compose up -d
```

### 5. Verificação da Instalação

Verifique se o container está em execução:

```bash
docker-compose ps
```

Teste o acesso ao collector:

```bash
curl -X GET http://localhost:8000/healthcheck \
  -H "Authorization: Bearer seu_token_secreto_aqui"
```

## Configuração de HTTPS (Opcional)

### Opção 1: Configuração Direta no Collector

Edite o arquivo `.env` e defina:

```
ENABLE_TLS=true
TLS_CERT_PATH=/certs/cert.pem
TLS_KEY_PATH=/certs/key.pem
```

Certifique-se de que os certificados estão disponíveis no diretório de volumes configurado.

### Opção 2: Usando Nginx como Reverse Proxy

1. Adicione o serviço Nginx ao arquivo `docker-compose.yml`:

```yaml
services:
  collector:
    # ... configuração existente ...
  
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
    depends_on:
      - collector
    restart: unless-stopped
```

2. Crie o arquivo de configuração do Nginx:

```bash
mkdir -p nginx
```

Crie o arquivo `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    server {
        listen 443 ssl;
        server_name your_server_name;

        ssl_certificate /etc/nginx/certs/cert.pem;
        ssl_certificate_key /etc/nginx/certs/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        location / {
            proxy_pass http://collector:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

3. Reinicie os serviços:

```bash
docker-compose down
docker-compose up -d
```

## Próximos Passos

Após a instalação bem-sucedida do Sentinel, você deve:

1. [Configurar o template no Zabbix](../guides/zabbix_configuration.md)
2. Configurar os hosts no Zabbix com as macros apropriadas
3. Verificar o funcionamento do monitoramento

## Solução de Problemas

Caso enfrente problemas durante a instalação:

- Verifique os logs do container: `docker-compose logs collector`
- Confirme as permissões dos arquivos de certificado (se usando HTTPS)
- Verifique se as portas não estão bloqueadas por firewall
- Confirme que o Zabbix consegue acessar o servidor do collector

Para mais ajuda, consulte o [Guia de Troubleshooting](troubleshooting.md).