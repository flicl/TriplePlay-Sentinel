#!/usr/bin/env python3
"""
Gunicorn Configuration for TriplePlay-Sentinel Collector
High-performance WSGI server configuration
"""

import os
import multiprocessing

# Server socket
bind = f"{os.getenv('COLLECTOR_HOST', '0.0.0.0')}:{os.getenv('COLLECTOR_PORT', '5000')}"
backlog = 2048

# Worker processes - Otimizado para poucos MikroTiks com muitas requisições cada
workers = int(os.getenv('GUNICORN_WORKERS', max(6, multiprocessing.cpu_count() * 3)))
worker_class = "gevent"
worker_connections = 1000  # 1000 conexões por worker para suportar carga alta
max_requests = 5000        # Mais requests antes de reciclar worker
max_requests_jitter = 200

# Timeout settings - Ajustado para comandos de rede
timeout = 120      # 2 minutos para comandos complexos (traceroute)
keepalive = 10     # Keep-alive mais longo para reutilizar conexões
graceful_timeout = 60

# Logging
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
accesslog = os.getenv('ACCESS_LOG', '-')  # stdout
errorlog = os.getenv('ERROR_LOG', '-')   # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'tripleplay-sentinel-collector'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL (se habilitado)
if os.getenv('ENABLE_HTTPS', 'false').lower() == 'true':
    keyfile = os.getenv('SSL_KEYFILE', '/app/ssl/key.pem')
    certfile = os.getenv('SSL_CERTFILE', '/app/ssl/cert.pem')

# Performance
preload_app = True
sendfile = True
reuse_port = True

# Memory management
max_requests_jitter = 50
preload_app = True

# Worker lifecycle
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("TriplePlay-Sentinel Collector starting...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("TriplePlay-Sentinel Collector reloading...")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"Worker {worker.pid} forked")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker {worker.pid} spawned")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")
