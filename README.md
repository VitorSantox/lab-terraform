# 🌐 Lab Terraform + GKE + Kubernetes

Este projeto é um **laboratório de aprendizado de SRE/DevOps** que demonstra como criar infraestrutura em Google Cloud usando **Terraform** e implantar aplicações simples no **Kubernetes (GKE)**.  

Ele foi projetado para **estudos e experimentação**, com configuração mínima (1 nó, máquina leve) para economizar custo.

---

## 📁 Estrutura do Projeto

```
lab-terraform/
├── README.md
├── terraform.tfstate
└── arquivos-terraform/
    ├── main.tf                  # Chama os módulos
    ├── provider.tf              # Provider GCP
    ├── variables.tf             # Variáveis globais
    ├── terraform.tfvars         # Valores das variáveis
    ├── outputs.tf               # Outputs gerais
    ├── .terraform.lock.hcl
    ├── terraform.tfstate
    ├── terraform.tfstate.backup
    ├── modules/
	├── gke/
	│   ├── main.tf
	│   ├── variables.tf
	│   └── outputs.tf
	├── pubsub/
	│   ├── main.tf
	│   ├── variables.tf
	│   └── outputs.tf
	└── sql/
	    ├── main.tf
	    ├── variables.tf
	    └── outputs.tf
├── k8s/
    ├── app1/
	│   ├── app1-deployment.yaml
	│   ├── app1-service.yaml
	│   ├── app1-secret.yaml
	│   └── app1-service.yaml
    ├── app1/
	│   ├── app2-deployment.yaml
	│   ├── app2-service.yaml
	│   ├── app2-secret.yaml
	│   └── app2-service.yaml
├── app1-produtora
  ├── Dockerfile
  ├── main.py (ou app.js)
  └── pubsub_client.py
├── app2-consumidora
  ├── Dockerfile
  ├── main.py (ou app.js)
  └── pubsub_client.py


```

---

## 🔧 Tecnologias utilizadas

- 🛠 **Terraform** → IaC (Infrastructure as Code) para criar e gerenciar o cluster GKE.  
- ☸️ **Google Kubernetes Engine (GKE)** → Cluster Kubernetes gerenciado.  
- 📦 **Kubernetes** → Deploy de aplicações (`app1` e `app2`) com Deployment e Service.  
- 💻 **Git/GitHub** → Versionamento e integração com pipeline de estudo.  

---

## ⚡ Fluxo do Projeto (Pipeline Conceitual)

```text
📄 Dev escreve Terraform (.tf)
           │
           ▼
🔀 Git Push / Pull Request
           │
           ▼
🤖 Pipeline CI/CD
           │
   ┌───────┼─────────┐
   │       │         │
  fmt   validate   plan
   │       │         │
   └───────┴─────────┘
           ▼
✅ terraform apply
           │
           ▼
☸️ Cluster GKE criado
           │
           ▼
🚀 kubectl apply -f k8s/
           │
           ▼
🎉 Apps rodando no cluster
```

---

## ⚙️ Comandos Terraform

1. **Inicializar o Terraform**  
```bash
terraform init
```

2. **Validar configuração**  
```bash
terraform validate
```

3. **Gerar plano de execução**  
```bash
terraform plan -out=plan.out
```

4. **Aplicar infraestrutura**  
```bash
terraform apply plan.out
```

5. **Destruir infraestrutura**  
```bash
terraform destroy
```
> ⚠️ Certifique-se de que `deletion_protection = false` no `main.tf` para poder destruir o cluster.

---

## 🖥️ Deploy de Aplicações Kubernetes

Após a criação do cluster:

```bash
# Configurar kubectl para o cluster
gcloud container clusters get-credentials gke-lab --region southamerica-east1 --project <PROJECT_ID>

# Aplicar deployments e services
kubectl apply -f k8s/
```

---

## 💡 Dicas de Estudo

- 🔹 Use máquinas pequenas (`e2-micro`) para economizar custo.  
- 🔹 Experimente mudar `node_count` e `machine_type` no `terraform.tfvars`.  
- 🔹 Sempre rode `terraform plan` antes de `apply` para entender mudanças.  
- 🔹 Evolua para pipeline CI/CD usando GitHub Actions ou GitLab CI.  
- 🔹 Explore **Workload Identity** e **Service Accounts** para aprender segurança em produção.  

---

## 🔗 Referências

- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)  
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)  
- [Kubernetes Docs](https://kubernetes.io/docs/home/)  

---

## 🚀 Resultado Esperado

- ✅ Cluster GKE leve com 1 nó.  
- ✅ Dois apps (`app1` e `app2`) rodando no cluster.  
- ✅ Experiência prática de **IaC + pipeline + deploy Kubernetes**.  
