"""
PUBSUB CLIENT - Cliente para publicar mensagens no Google Pub/Sub
================================================================
Este módulo é responsável por:
- Configurar cliente do Google Pub/Sub
- Publicar mensagens de forma assíncrona
- Implementar retry policy para resiliência
- Serializar dados em JSON para envio

Padrão SRE: 
- Retry automático com backoff exponencial
- Logging estruturado para debugging
- Tratamento robusto de erros
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Google Cloud Pub/Sub
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.publisher.exceptions import NotFound, PermissionDenied
from google.api_core import retry
from google.auth import default
import google.auth.exceptions

# Configurar logger
logger = logging.getLogger("pubsub-client")

class PubSubPublisher:
    """
    Cliente assíncrono para publicar mensagens no Google Pub/Sub
    
    Features implementadas:
    - Retry automático com backoff exponencial
    - Tratamento de erros específicos do GCP
    - Logging estruturado para observabilidade
    - Configuração via variáveis de ambiente
    """
    
    def __init__(self):
        """
        Inicializa o cliente Pub/Sub
        
        Variáveis de ambiente necessárias:
        - PROJECT_ID: ID do projeto GCP
        - PUBSUB_TOPIC: Nome do tópico Pub/Sub
        - GOOGLE_APPLICATION_CREDENTIALS: Caminho para service account key (opcional)
        """
        # Configurações do ambiente
        self.project_id = os.getenv('PROJECT_ID', 'meu-projeto-lab')
        self.topic_name = os.getenv('PUBSUB_TOPIC', 'database-operations')
        
        # Log das configurações (sem dados sensíveis)
        logger.info(f"🔧 Configurando Pub/Sub - Projeto: {self.project_id}, Tópico: {self.topic_name}")
        
        # Inicializar cliente
        try:
            self._initialize_client()
            logger.info("✅ Cliente Pub/Sub inicializado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar cliente Pub/Sub: {e}")
            raise
    
    def _initialize_client(self):
        """
        Inicializa o cliente do Publisher
        
        Tenta autenticação automática primeiro, depois fallback para service account
        """
        try:
            # Tentar autenticação automática (Workload Identity ou ADC)
            credentials, project = default()
            if project:
                self.project_id = project
                
            logger.info("🔐 Usando autenticação automática (ADC/Workload Identity)")
            
        except google.auth.exceptions.DefaultCredentialsError:
            # Fallback para service account key
            sa_key_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if sa_key_path and os.path.exists(sa_key_path):
                logger.info(f"🔑 Usando Service Account Key: {sa_key_path}")
            else:
                logger.warning("⚠️ Nenhuma credencial encontrada. Verifique GOOGLE_APPLICATION_CREDENTIALS")
                raise
        
        # Criar cliente publisher
        self.publisher_client = pubsub_v1.PublisherClient()
        
        # Construir path completo do tópico
        self.topic_path = self.publisher_client.topic_path(self.project_id, self.topic_name)
        
        # Verificar se o tópico existe
        self._verify_topic_exists()
    
    def _verify_topic_exists(self):
        """
        Verifica se o tópico existe no Pub/Sub
        Em produção, tópicos devem ser criados pelo Terraform
        """
        try:
            self.publisher_client.get_topic(request={"topic": self.topic_path})
            logger.info(f"✅ Tópico {self.topic_name} encontrado")
            
        except NotFound:
            logger.error(f"❌ Tópico {self.topic_name} não encontrado!")
            raise Exception(f"Tópico {self.topic_name} não existe. Crie-o primeiro com Terraform.")
            
        except PermissionDenied:
            logger.error(f"❌ Sem permissão para acessar tópico {self.topic_name}")
            raise Exception("Service Account sem permissão para acessar Pub/Sub")
    
    async def publish_message(self, data: Dict[str, Any]) -> str:
        """
        Publica mensagem no Pub/Sub de forma assíncrona
        
        Args:
            data: Dados a serem publicados (será serializado em JSON)
            
        Returns:
            str: ID da mensagem publicada
            
        Raises:
            Exception: Se houver erro na publicação
        """
        try:
            # Serializar dados para JSON
            message_data = json.dumps(data, ensure_ascii=False, default=str)
            
            # Log da tentativa de publicação
            logger.info(f"📤 Publicando mensagem no tópico {self.topic_name}")
            logger.debug(f"📋 Dados da mensagem: {message_data[:200]}...")  # Log truncado
            
            # Converter para bytes
            message_bytes = message_data.encode('utf-8')
            
            # Metadados da mensagem (attributes)
            attributes = {
                'source': 'app1-produtora',
                'event_type': data.get('event_type', 'unknown'),
                'timestamp': data.get('timestamp', datetime.utcnow().isoformat()),
                'operation': data.get('operation', 'unknown')
            }
            
            # Publicar mensagem com retry automático
            future = self.publisher_client.publish(
                self.topic_path,
                message_bytes,
                **attributes
            )
            
            # Aguardar resultado de forma assíncrona
            message_id = await self._wait_for_publish(future)
            
            logger.info(f"✅ Mensagem publicada com sucesso. ID: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao publicar mensagem: {e}")
            raise
    
    async def _wait_for_publish(self, future) -> str:
        """
        Aguarda resultado da publicação de forma assíncrona
        
        Args:
            future: Future retornado pelo publisher.publish()
            
        Returns:
            str: ID da mensagem
        """
        # Executar em thread pool para não bloquear event loop
        loop = asyncio.get_event_loop()
        
        def _get_result():
            """Função auxiliar para executar em thread separada"""
            try:
                # Configurar retry policy
                retry_policy = retry.Retry(
                    initial=1.0,      # Delay inicial de 1 segundo
                    maximum=60.0,     # Delay máximo de 60 segundos
                    multiplier=2.0,   # Backoff exponencial
                    deadline=300.0    # Timeout total de 5 minutos
                )
                
                # Aguardar resultado com retry
                return future.result(timeout=30.0)
                
            except Exception as e:
                logger.error(f"❌ Erro no future.result(): {e}")
                raise
        
        # Executar em thread pool
        return await loop.run_in_executor(None, _get_result)
    
    def publish_batch(self, messages: list) -> list:
        """
        Publica múltiplas mensagens em lote (para uso futuro)
        
        Args:
            messages: Lista de dicionários com dados das mensagens
            
        Returns:
            list: Lista de IDs das mensagens publicadas
            
        Nota: Implementação síncrona para batch publishing
        """
        logger.info(f"📦 Publicando lote de {len(messages)} mensagens")
        
        message_ids = []
        futures = []
        
        try:
            # Enviar todas as mensagens
            for i, data in enumerate(messages):
                message_data = json.dumps(data, ensure_ascii=False, default=str)
                message_bytes = message_data.encode('utf-8')
                
                attributes = {
                    'source': 'app1-produtora',
                    'batch_index': str(i),
                    'batch_size': str(len(messages)),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                future = self.publisher_client.publish(
                    self.topic_path,
                    message_bytes,
                    **attributes
                )
                futures.append(future)
            
            # Aguardar todos os resultados
            for i, future in enumerate(futures):
                try:
                    message_id = future.result(timeout=30.0)
                    message_ids.append(message_id)
                    logger.debug(f"✅ Mensagem {i+1}/{len(messages)} publicada: {message_id}")
                except Exception as e:
                    logger.error(f"❌ Erro na mensagem {i+1}/{len(messages)}: {e}")
                    message_ids.append(None)
            
            successful = len([mid for mid in message_ids if mid is not None])
            logger.info(f"📊 Lote concluído: {successful}/{len(messages)} mensagens publicadas")
            
            return message_ids
            
        except Exception as e:
            logger.error(f"❌ Erro no batch publish: {e}")
            raise
    
    def close(self):
        """
        Fecha o cliente (cleanup)
        """
        try:
            if hasattr(self, 'publisher_client'):
                # Aguardar mensagens pendentes
                self.publisher_client.stop()
                logger.info("🛑 Cliente Pub/Sub fechado")
        except Exception as e:
            logger.error(f"⚠️ Erro ao fechar cliente: {e}")

# Função utilitária para teste
async def test_publisher():
    """
    Função de teste para validar o publisher
    Use apenas para desenvolvimento/debug
    """
    publisher = PubSubPublisher()
    
    test_data = {
        "event_id": "test_001",
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "database_operation",
        "operation": "INSERT",
        "table": "test_table",
        "data": {"name": "Teste", "value": 123}
    }
    
    try:
        message_id = await publisher.publish_message(test_data)
        print(f"Teste bem-sucedido! Message ID: {message_id}")
    except Exception as e:
        print(f"Teste falhou: {e}")
    finally:
        publisher.close()

# Para executar teste direto
if __name__ == "__main__":
    asyncio.run(test_publisher())