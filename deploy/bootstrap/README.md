
### ArgoCD
ArgoCD changes must be applied using patches in k8s/argocd folder

argocd account generate-token --account admin


### CNPG 

k create ns cnpg

psql -h 192.168.x.x

```
CREATE SCHEMA todo;

ALTER USER todo_db_admin SET search_path TO todo;
```


### Github Setup
four github secrets
ARGOCD_TOKEN
DOCKERHUB_TOKEN
DOCKERHUB_USERNAME
GH_ACCESS_TOKEN

todo-platform variable
ARGOCD_LOCK