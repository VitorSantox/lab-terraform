variable "project_id" {               # Projeto GCP (opcional se provider já setar)
  type = string
}

variable "topic_name" {               # Nome do tópico Pub/Sub
  type = string
}

variable "subscription_name" {        # Nome da assinatura
  type = string
}

variable "ack_deadline_seconds" {     # Tempo p/ ack de mensagens (segundos)
  type    = number
  default = 20
}
