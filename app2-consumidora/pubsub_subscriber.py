"""
pubsub_subscriber.py
--------------------
Módulo responsável por consumir mensagens do Google Pub/Sub.
- Conecta na subscription configurada.
- Processa mensagens recebidas e aplica lógica de persistência no banco.
- Gera métricas de mensagens recebidas/ack/nack.
"""

import json
import asyncio
import logging
from typing import Any, Dict
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.message import Message

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class PubSubSubscriber:
    def __init__(self, project_id: str, subscription_id: str, message_processor):
        self.project_id = project_id
        self.subscription_id = subscription_id
        self.message_processor = message_processor
        self.subscriber_client = pubsub_v1.SubscriberClient()
        self.subscription_path = self.subscriber_client.subscription_path(project_id, subscription_id)
        self.streaming_pull_future = None
        self.is_consuming = False
        self.metrics = {
            "messages_received": 0,
            "messages_acked": 0,
            "messages_nacked": 0
        }

    def _callback(self, message: Message):
        self.metrics["messages_received"] += 1
        logger.info(f"📩 Mensagem recebida: {message.message_id}")

        try:
            data = json.loads(message.data.decode("utf-8"))
            success = asyncio.run_coroutine_threadsafe(
                self.message_processor.process_message(data),
                asyncio.get_event_loop()
            ).result()

            if success:
                message.ack()
                self.metrics["messages_acked"] += 1
            else:
                message.nack()
                self.metrics["messages_nacked"] += 1

        except Exception as e:
            logger.error(f"❌ Erro no callback: {e}")
            message.nack()

    def start_consuming(self):
        flow_control = pubsub_v1.types.FlowControl(max_messages=10)
        self.streaming_pull_future = self.subscriber_client.subscribe(
            self.subscription_path,
            callback=self._callback,
            flow_control=flow_control
        )
        self.is_consuming = True
        logger.info("🚀 Subscriber iniciado e escutando mensagens")

    async def stop_consuming(self):
        if self.streaming_pull_future:
            self.streaming_pull_future.cancel()
            self.is_consuming = False
            logger.info("🛑 Subscriber parado")
