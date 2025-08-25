# GKE
output "gke_cluster_name" {       value = module.gke.cluster_name }
output "gke_endpoint"     {       value = module.gke.endpoint }
output "gke_node_pool"    {       value = module.gke.node_pool_name }
output "gke_node_count"   {       value = module.gke.node_count }

# Pub/Sub
output "pubsub_topic"      {      value = module.pubsub.topic }
output "pubsub_subscription"{     value = module.pubsub.subscription }

# SQL
output "sql_connection"    {      value = module.sql.instance_connection_name }
output "sql_public_ip"     {      value = module.sql.public_ip }
output "sql_database"      {      value = module.sql.database }
output "sql_user"          {      value = module.sql.db_user }
