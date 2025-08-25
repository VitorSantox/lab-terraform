resource "google_pubsub_topic" "topic" {    # Cria o tópico
  name = var.topic_name                     # Nome do tópico (ex.: api-events)
}

resource "google_pubsub_subscription" "sub" {  # Cria a assinatura do tópico
  name  = var.subscription_name                # Nome da subscription
  topic = google_pubsub_topic.topic.name       # Liga àquele tópico
  ack_deadline_seconds = var.ack_deadline_seconds # Janela para processar e dar ack
}
