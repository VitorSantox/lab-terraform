# APP1-PRODUTORA DOCKERFILE
# ========================
# Multi-stage build para otimizar tamanho da imagem
# Baseado em Python slim para reduzir superfície de ataque
# Inclui boas práticas de segurança e performance

# Build Stage - instala dependências
FROM python:3.11-slim as builder

# Metadados da imagem
LABEL maintainer="seu-email@exemplo.com" \
      description="App1 Produtora - API FastAPI para publicar eventos no Pub/Sub" \
      version="1.0.0"

# Instalar dependências de sistema necessárias para build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /build

# Copiar requirements primeiro (para aproveitar cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Production Stage - imagem final
FROM python:3.11-slim

# Instalar apenas dependências runtime necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    # curl para health checks
    curl \
    # ca-certificates para HTTPS
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Criar usuário não-root para segurança
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Criar diretórios necessários
RUN mkdir -p /app /app/logs && \
    chown -R appuser:appuser /app

# Copiar dependências instaladas do build stage
COPY --from=builder /root/.local /home/appuser/.local

# Definir diretório de trabalho
WORKDIR /app

# Copiar código da aplicação
COPY --chown=appuser:appuser main.py .
COPY --chown=appuser:appuser pubsub_client.py .

# Alterar para usuário não-root
USER appuser

# Adicionar diretório local do usuário ao PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Configurações da aplicação
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Variáveis de ambiente para FastAPI
ENV FASTAPI_ENV=production
ENV PORT=8000

# Expor porta da aplicação
EXPOSE 8000

# Health check (usado pelo Docker e Kubernetes)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando padrão - usar uvicorn em produção
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# Para desenvolvimento local, pode usar:
# CMD ["python", "main.py"]