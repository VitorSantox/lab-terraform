output "topic" {             # Exibe nome do tópico
  value = google_pubsub_topic.topic.name
}

output "subscription" {      # Exibe nome da assinatura
  value = google_pubsub_subscription.sub.name
}
