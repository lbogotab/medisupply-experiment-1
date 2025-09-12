## Política de AWS Load Balancer Controller

# 1. Descargar la versión oficial de la policy (ajusta v2.13.4 si cambia la versión del controller)
```bash
curl -L -o iam_policy_alb.json \
  https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.13.4/docs/install/iam_policy.json
```

# 2. Crear la policy si no existe todavía
```bash
aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam_policy_alb.json
```

# 3. (Si ya existe) Crear una nueva versión y marcarla como default
```bash
POLICY_ARN=$(aws iam list-policies \
  --query "Policies[?PolicyName=='AWSLoadBalancerControllerIAMPolicy'].Arn | [0]" \
  --output text)

aws iam create-policy-version \
  --policy-arn $POLICY_ARN \
  --policy-document file://iam_policy_alb.json \
  --set-as-default
```

## Instalar AWS Load Balancer Controller

> Ejecutar estos comandos después de crear el cluster y la ServiceAccount para el ALB Controller.

```bash
helm repo add eks https://aws.github.io/eks-charts
helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=miso-eks-default \
  --set region=us-east-1 \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

kubectl -n kube-system rollout status deploy/aws-load-balancer-controller

