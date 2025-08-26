"""
APP1-PRODUTORA - API REST com FastAPI
====================================
Esta aplicação é responsável por:
- Receber requisições HTTP POST com dados de operações de banco
- Publicar eventos no Google Pub/Sub para serem consumidos pela app2
- Fornecer endpoints de observabilidade (health checks)
- Implementar logging estruturado e métricas básicas

Fluxo: HTTP POST -> Validação -> Pub/Sub Publish -> Response
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

# FastAPI e dependências
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# Cliente Pub/Sub
from pubsub_client import PubSubPublisher

# Configuração de logging estruturado (importante para observabilidade)
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(name)s"}',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("app1-produtora")

# Modelos Pydantic para validação de entrada
class DatabaseOperation(BaseModel):
    """
    Modelo que define as operações permitidas no banco de dados
    - operation: tipo da operação (INSERT, UPDATE, DELETE)
    - table: nome da tabela alvo
    - data: dados para a operação (opcional para DELETE)
    - where_clause: condição WHERE (para UPDATE e DELETE)
    """
    operation: str = Field(..., description="Tipo de operação: INSERT, UPDATE ou DELETE")
    table: str = Field(..., min_length=1, description="Nome da tabela")
    data: Optional[Dict[str, Any]] = Field(None, description="Dados para INSERT/UPDATE")
    where_clause: Optional[Dict[str, Any]] = Field(None, description="Condições WHERE para UPDATE/DELETE")
    
    @validator('operation')
    def validate_operation(cls, v):
        """Valida se a operação é permitida"""
        allowed_operations = ['INSERT', 'UPDATE', 'DELETE']
        if v.upper() not in allowed_operations:
            raise ValueError(f'Operação deve ser uma de: {allowed_operations}')
        return v.upper()
    
    @validator('data')
    def validate_data_for_insert_update(cls, v, values):
        """Valida se dados são fornecidos para INSERT/UPDATE"""
        operation = values.get('operation', '').upper()
        if operation in ['INSERT', UPDATE'] and not v:
            raise ValueError(f'Campo data é obrigatório para operação {operation}')
        return v

# Variáveis globais para métricas simples (em produção, usar Prometheus)
metrics = {
    "total_requests": 0,
    "successful_publishes": 0,
    "failed_publishes": 0,
    "start_time": datetime.utcnow()
}

# Lifespan manager para inicializar/finalizar recursos
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação
    - Startup: inicializa cliente Pub/Sub
    - Shutdown: limpa recursos
    """
    logger.info("🚀 Inicializando app1-produtora...")
    
    # Inicializar cliente Pub/Sub
    try:
        app.state.pubsub_publisher = PubSubPublisher()
        logger.info("✅ Cliente Pub/Sub inicializado com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar Pub/Sub: {e}")
        raise
    
    yield  # Aplicação roda aqui
    
    # Cleanup
    logger.info("🛑 Finalizando app1-produtora...")

# Inicializar FastAPI com lifespan
app = FastAPI(
    title="App1 Produtora",
    description="API REST que publica eventos de operações de banco no Pub/Sub",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware para logging de requests (observabilidade)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware que loga todas as requisições HTTP
    Importante para observabilidade e debugging
    """
    start_time = time.time()
    
    # Log da requisição entrante
    logger.info(f"📨 Request: {request.method} {request.url.path}")
    
    # Processar requisição
    response = await call_next(request)
    
    # Calcular tempo de processamento
    process_time = time.time() - start_time
    
    # Log da resposta
    logger.info(f"📤 Response: {response.status_code} - {process_time:.3f}s")
    
    # Adicionar header com tempo de processamento
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

@app.get("/")
async def root():
    """
    Endpoint raiz - informações básicas da API
    """
    return {
        "service": "app1-produtora",
        "version": "1.0.0",
        "status": "running",
        "description": "API REST para publicar eventos de operações de banco"
    }

@app.get("/health")
async def health_check():
    """
    Health Check Endpoint - usado pelo Kubernetes para verificar se a aplicação está saudável
    
    Verifica:
    - Se a aplicação está respondendo
    - Se o cliente Pub/Sub está funcionando
    
    Retorna HTTP 200 se tudo OK, HTTP 503 se há problemas
    """
    try:
        # Verificar se o cliente Pub/Sub está disponível
        if hasattr(app.state, 'pubsub_publisher'):
            # Aqui poderíamos fazer um teste real de conectividade
            health_status = "healthy"
            status_code = status.HTTP_200_OK
        else:
            health_status = "unhealthy"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            
        return JSONResponse(
            status_code=status_code,
            content={
                "status": health_status,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "app1-produtora",
                "checks": {
                    "pubsub_client": "ok" if hasattr(app.state, 'pubsub_publisher') else "fail"
                }
            }
        )
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )

@app.get("/ready")
async def readiness_check():
    """
    Readiness Check - usado pelo Kubernetes para verificar se a aplicação está pronta para receber tráfego
    
    Diferente do health check, este verifica se todas as dependências estão prontas
    """
    try:
        # Verificar se todas as dependências estão prontas
        dependencies_ready = hasattr(app.state, 'pubsub_publisher')
        
        if dependencies_ready:
            return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready", "timestamp": datetime.utcnow().isoformat()}
            )
    except Exception as e:
        logger.error(f"❌ Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "error": str(e)}
        )

@app.get("/metrics")
async def get_metrics():
    """
    Endpoint de métricas básicas - em produção, integrar com Prometheus
    
    Retorna métricas importantes para monitoramento:
    - Total de requisições processadas
    - Sucessos e falhas na publicação
    - Tempo de uptime
    """
    uptime_seconds = (datetime.utcnow() - metrics["start_time"]).total_seconds()
    
    return {
        "metrics": {
            "total_requests": metrics["total_requests"],
            "successful_publishes": metrics["successful_publishes"],
            "failed_publishes": metrics["failed_publishes"],
            "uptime_seconds": uptime_seconds,
            "success_rate": (
                metrics["successful_publishes"] / max(metrics["total_requests"], 1) * 100
            )
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/database-operation")
async def publish_database_operation(operation: DatabaseOperation):
    """
    Endpoint principal - recebe operação de banco e publica no Pub/Sub
    
    Args:
        operation: Dados da operação (INSERT, UPDATE, DELETE)
        
    Returns:
        JSON com status da publicação e ID da mensagem
        
    Raises:
        HTTPException: Se houver erro na validação ou publicação
    """
    # Incrementar contador de requisições
    metrics["total_requests"] += 1
    
    try:
        # Log da operação recebida
        logger.info(f"📋 Operação recebida: {operation.operation} na tabela {operation.table}")
        
        # Criar evento para publicar no Pub/Sub
        event_data = {
            "event_id": f"evt_{int(time.time())}_{metrics['total_requests']}",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "app1-produtora",
            "event_type": "database_operation",
            "operation": operation.operation,
            "table": operation.table,
            "data": operation.data,
            "where_clause": operation.where_clause
        }
        
        # Publicar no Pub/Sub
        message_id = await app.state.pubsub_publisher.publish_message(event_data)
        
        # Incrementar contador de sucessos
        metrics["successful_publishes"] += 1
        
        # Log de sucesso
        logger.info(f"✅ Evento publicado com sucesso. Message ID: {message_id}")
        
        return {
            "status": "success",
            "message": "Operação publicada com sucesso",
            "event_id": event_data["event_id"],
            "message_id": message_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        # Incrementar contador de falhas
        metrics["failed_publishes"] += 1
        
        # Log do erro
        logger.error(f"❌ Erro ao publicar evento: {e}")
        
        # Retornar erro HTTP
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Falha ao publicar operação",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Handler de exceções globais
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler global para exceções não tratadas
    Importante para observabilidade - captura erros inesperados
    """
    logger.error(f"❌ Exceção não tratada: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Erro interno do servidor",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    # Para desenvolvimento local
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)