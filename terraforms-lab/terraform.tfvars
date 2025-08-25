project_id = "devops-466923"
region = "southamerica-east1"

cluster_name = "terraform-cluster-lab-5"
node_count = 1
machine_type = "e2-micro"
disk_size = 30
disk_type = "pd-standard"

pubsub_topic_name        = "api-events"
pubsub_subscription_name = "api-events-sub"

db_instance_name = "lab-postgres"
db_version       = "POSTGRES_15"
db_tier          = "db-f1-micro"
db_name          = "appdb"
db_user          = "appuser"
# db_password    = "NÃO COLOQUE AQUI EM PROD"  # use TF_VAR_db_password no shell