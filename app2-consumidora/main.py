"""
APP2-CONSUMIDORA - Worker assíncrono para consumir Pub/Sub e executar operações no banco
=======================================================================================
Esta aplicação é responsável por:
- Consumir mensagens do Google Pub/Sub de forma assíncrona
- Processar eventos de operações de banco (INSERT, UPDATE, DELETE)
- Executar operações no banco de dados PostgreSQL
- Implementar retry automático e dead letter queue
- Fornecer observabilidade e health checks para Kubernetes

Fluxo: Pub/Sub Subscribe -> Validação -> Database Operation -> ACK/NACK
"""

import os
import json
import logging
import asyncio
import signal
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

# FastAPI para health checks (não para servir requests HTTP)
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

# Cliente Pub/Sub e Database
from pubsub_subscriber import PubSubSubscriber
from database_client import DatabaseClient

# Configuração de logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(name)s"}',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("app2-consumidora")

# Variáveis globais para métricas
metrics = {
    "messages_received": 0,
    "messages_processed": 0,
    "messages_failed": 0,
    "database_operations_success": 0,
    "database_operations_failed": 0,
    "start_time": datetime.utcnow()
}

class MessageProcessor:
    """
    Classe responsável por processar mensagens do Pub/Sub
    
    Implementa:
    - Validação de mensagens
    - Mapeamento de operações para SQL
    - Retry logic para falhas
    - Dead letter queue para mensagens inválidas
    """
    
    def __init__(self, db_client: DatabaseClient):
        """
        Inicializa o processador de mensagens
        
        Args:
            db_client: Cliente do banco de dados
        """
        self.db_client = db_client
        self.logger = logging.getLogger("message-processor")
    
    async def process_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Processa uma mensagem do Pub/Sub
        
        Args:
            message_data: Dados da mensagem decodificada
            
        Returns:
            bool: True se processamento foi bem-sucedido, False caso contrário
        """
        try:
            # Incrementar contador de mensagens recebidas
            metrics["messages_received"] += 1
            
            # Log da mensagem recebida
            self.logger.info(f"📨 Processando mensagem: {message_data.get('event_id', 'unknown')}")
            
            # Validar estrutura da mensagem
            if not self._validate_message(message_data):
                self.logger.error("❌ Mensagem inválida - estrutura incorreta")
                metrics["messages_failed"] += 1
                return False  # NACK - mensagem vai para DLQ
            
            # Extrair dados da operação
            operation = message_data.get('operation', '').upper()
            table = message_data.get('table', '')
            data = message_data.get('data', {})
            where_clause = message_data.get('where_clause', {})
            
            # Executar operação no banco
            success = await self._execute_database_operation(
                operation, table, data, where_clause
            )
            
            if success:
                metrics["messages_processed"] += 1
                metrics["database_operations_success"] += 1
                self.logger.info(f"✅ Mensagem processada com sucesso")
                return True  # ACK
            else:
                metrics["messages_failed"] += 1
                metrics["database_operations_failed"] += 1
                self.logger.error(f"❌ Falha ao processar mensagem")
                return False  # NACK - retry automático
                
        except Exception as e:
            metrics["messages_failed"] += 1
            self.logger.error(f"❌ Erro inesperado ao processar mensagem: {e}")
            return False  # NACK - retry automático
    
    def _validate_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Valida se a mensagem tem estrutura válida
        
        Args:
            message_data: Dados da mensagem
            
        Returns:
            bool: True se válida
        """
        required_fields = ['operation', 'table', 'event_type']
        
        # Verificar campos obrigatórios
        for field in required_fields:
            if field not in message_data:
                self.logger.error(f"Campo obrigatório ausente: {field}")
                return False
        
        # Verificar se é evento de database operation
        if message_data.get('event_type') != 'database_operation':
            self.logger.error(f"Tipo de evento inválido: {message_data.get('event_type')}")
            return False
        
        # Verificar operação válida
        operation = message_data.get('operation', '').upper()
        valid_operations = ['INSERT', 'UPDATE', 'DELETE']
        if operation not in valid_operations:
            self.logger.error(f"Operação inválida: {operation}")
            return False
        
        # Validações específicas por operação
        if operation == 'INSERT':
            if not message_data.get('data'):
                self.logger.error("INSERT requer campo 'data'")
                return False
                
        elif operation == 'UPDATE':
            if not message_data.get('data') or not message_data.get('where_clause'):
                self.logger.error("UPDATE requer campos 'data' e 'where_clause'")
                return False
                
        elif operation == 'DELETE':
            if not message_data.get('where_clause'):
                self.logger.error("DELETE requer campo 'where_clause'")
                return False
        
        return True
    
    async def _execute_database_operation(
        self, 
        operation: str, 
        table: str, 
        data: Dict[str, Any], 
        where_clause: Dict[str, Any]
    ) -> bool:
        """
        Executa operação no banco de dados
        
        Args:
            operation: Tipo de operação (INSERT, UPDATE, DELETE)
            table: Nome da tabela
            data: Dados para INSERT/UPDATE
            where_clause: Condições WHERE para UPDATE/DELETE
            
        Returns:
            bool: True se operação foi bem-sucedida
        """
        try:
            self.logger.info(f"🗄️ Executando {operation} na tabela {table}")
            
            if operation == 'INSERT':
                result = await self.db_client.insert(table, data)
                
            elif operation == 'UPDATE':
                result = await self.db_client.update(table, data, where_clause)
                
            elif operation == 'DELETE':
                result = await self.db_client.delete(table, where_clause)
            
            else:
                self.logger.error(f"Operação não implementada: {operation}")
                return False
            
            self.logger.info(f"✅ Operação {operation} executada com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro na operação {operation}: {e}")
            return False

# Variáveis globais para o worker
subscriber: Optional[PubSubSubscriber] = None
processor: Optional[MessageProcessor] = None
running = False

async def start_consumer():
    """
    Inicia o consumer principal
    """
    global subscriber, processor, running
    
    try:
        # Inicializar cliente do banco
        db_client = DatabaseClient()
        await db_client.connect()
        
        # Inicializar processador de mensagens
        processor = MessageProcessor(db_client)
        
        # Inicializar subscriber do Pub/Sub
        subscriber = PubSubSubscriber(processor)
        
        logger.info("🚀 Iniciando consumer de mensagens...")
        running = True
        
        # Iniciar consumo (blocking)
        await subscriber.start_consuming()
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar consumer: {e}")
        running = False
        raise

async def stop_consumer():
    """
    Para o consumer gracefully
    """
    global subscriber, running
    
    logger.info("🛑 Parando consumer...")
    running = False
    
    if subscriber:
        await subscriber.stop_consuming()

# Signal handlers para shutdown graceful
def signal_handler(signum, frame):
    """
    Handler para sinais do sistema (SIGTERM, SIGINT)
    Importante para shutdown graceful no Kubernetes
    """
    logger.info(f"📡 Sinal recebido: {signum}")
    asyncio.create_task(stop_consumer())

# Registrar signal handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Kubernetes termination

# FastAPI app para health checks (roda em paralelo ao consumer)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia ciclo de vida da aplicação
    """
    logger.info("🚀 Inicializando app2-consumidora...")
    yield
    logger.info("🛑 Finalizando app2-consumidora...")

app = FastAPI(
    title="App2 Consumidora",
    description="Worker que consome eventos Pub/Sub e executa operações no banco",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """
    Endpoint raiz
    """
    return {
        "service": "app2-consumidora",
        "version": "1.0.0",
        "status": "running" if running else "stopped",
        "description": "Worker assíncrono para processar eventos de banco via Pub/Sub"
    }

@app.get("/health")
async def health_check():
    """
    Health check para Kubernetes liveness probe
    Verifica se o worker está funcionando
    """
    try:
        # Verificar se consumer está rodando
        is_healthy = running and subscriber is not None
        
        if is_healthy:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "consumer_running": running,
                    "uptime_seconds": (datetime.utcnow() - metrics["start_time"]).total_seconds()
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unhealthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "consumer_running": running
                }
            )
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.get("/ready")
async def readiness_check():
    """
    Readiness check para Kubernetes readiness probe
    Verifica se todas as dependências estão prontas
    """
    try:
        # Verificar dependências
        dependencies_ready = (
            running and 
            subscriber is not None and 
            processor is not None
        )
        
        if dependencies_ready:
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
                "dependencies": {
                    "pubsub_subscriber": "ready",
                    "database_client": "ready",
                    "message_processor": "ready"
                }
            }
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not_ready",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.get("/metrics")
async def get_metrics():
    """
    Endpoint de métricas para monitoramento
    """
    uptime_seconds = (datetime.utcnow() - metrics["start_time"]).total_seconds()
    
    # Calcular taxa de sucesso
    total_processed = metrics["messages_processed"] + metrics["messages_failed"]
    success_rate = (
        (metrics["messages_processed"] / max(total_processed, 1)) * 100
        if total_processed > 0 else 0
    )
    
    return {
        "metrics": {
            "messages_received": metrics["messages_received"],
            "messages_processed": metrics["messages_processed"],
            "messages_failed": metrics["messages_failed"],
            "database_operations_success": metrics["database_operations_success"],
            "database_operations_failed": metrics["database_operations_failed"],
            "success_rate_percent": round(success_rate, 2),
            "uptime_seconds": uptime_seconds,
            "consumer_status": "running" if running else "stopped"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# Função principal para executar consumer + API
async def main():
    """
    Função principal que executa consumer e API em paralelo
    """
    logger.info("🚀 Iniciando app2-consumidora...")
    
    try:
        # Criar tasks para consumer e API
        consumer_task = asyncio.create_task(start_consumer())
        
        # Para desenvolvimento local, pode rodar uvicorn aqui
        # Em produção, uvicorn roda via Dockerfile
        
        # Aguardar consumer
        await consumer_task
        
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown solicitado pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro na aplicação: {e}")
    finally:
        await stop_consumer()

if __name__ == "__main__":
    # Executar aplicação
    asyncio.run(main())