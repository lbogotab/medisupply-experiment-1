# Experimento MediSupply 1

El Experimento 1 busca validar la capacidad de la arquitectura de MediSupply desplegada en Amazon EKS para sostener escenarios de carga extrema, asegurando que el sistema responda de manera estable ante picos de 400 pedidos por minuto sin pérdida de información. El propósito es comprobar la efectividad del autoscaling de pods y nodos, así como la resiliencia de componentes críticos como API Gateway, DynamoDB y SQS, manteniendo tiempos de respuesta inferiores a un segundo y disponibilidad continua.

<img width="2529" height="1585" alt="Proyecto Integrador - s6 - experimento 1" src="https://github.com/user-attachments/assets/bdb512cd-1d09-4a57-ae6a-2fea557e6ffa" />

## 1. Creación del cluster EKS

Para iniciar el experimento, se creó un cluster de Kubernetes gestionado por EKS con `eksctl`, configurando una VPC con subredes públicas y privadas, así como grupos de nodos gestionados.

### Archivo YAML ejemplo (`cluster.yaml`):

```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: miso-eks-default
  region: us-east-1

vpc:
  cidr: "10.0.0.0/16"
  subnets:
    public:
      public-subnet-1:
        cidr: "10.0.1.0/24"
      public-subnet-2:
        cidr: "10.0.2.0/24"
    private:
      private-subnet-1:
        cidr: "10.0.101.0/24"
      private-subnet-2:
        cidr: "10.0.102.0/24"

managedNodeGroups:
  - name: managed-ng-1
    instanceType: t3.medium
    desiredCapacity: 2
    privateNetworking: true
```

### Comando para crear el cluster:

```bash
eksctl create cluster -f cluster.yaml
```

### Verificación del cluster:

```bash
aws eks update-kubeconfig --region us-east-1 --name miso-eks-default
kubectl get nodes
kubectl get pods --all-namespaces
```
### Política de AWS Load Balancer Controller

### 1.1 Descargar la versión oficial de la policy (ajusta v2.13.4 si cambia la versión del controller)
```bash
curl -L -o iam_policy_alb.json \
  https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.13.4/docs/install/iam_policy.json
```

### 1.2 Crear la policy si no existe todavía
```bash
aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam_policy_alb.json
```

### 1.3 (Si ya existe) Crear una nueva versión y marcarla como default
```bash
POLICY_ARN=$(aws iam list-policies \
  --query "Policies[?PolicyName=='AWSLoadBalancerControllerIAMPolicy'].Arn | [0]" \
  --output text)

aws iam create-policy-version \
  --policy-arn $POLICY_ARN \
  --policy-document file://iam_policy_alb.json \
  --set-as-default
```

### 1.4 Instalar AWS Load Balancer Controller

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
```
---

## 2. Despliegue de microservicios

El repositorio del proyecto contiene dos microservicios en carpetas separadas:

```
/micro1
/micro2
```

Cada microservicio tiene su propio `Dockerfile`, código fuente y manifiestos Kubernetes (`Deployment.yaml`, `Service.yaml`, `Ingress.yaml`).

### Construcción y subida de imágenes a Amazon ECR con GitHub Actions

Se configuró un workflow en GitHub Actions para automatizar la construcción y publicación de imágenes:

```yaml
name: Build and Push to ECR

on:
  push:
    branches:
      - main

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build, tag, and push micro1 image
        run: |
          docker build -t micro1 ./micro1
          docker tag micro1:latest ${{ secrets.ECR_REGISTRY }}/micro1:latest
          docker push ${{ secrets.ECR_REGISTRY }}/micro1:latest

      - name: Build, tag, and push micro2 image
        run: |
          docker build -t micro2 ./micro2
          docker tag micro2:latest ${{ secrets.ECR_REGISTRY }}/micro2:latest
          docker push ${{ secrets.ECR_REGISTRY }}/micro2:latest
```

### Despliegue en Kubernetes

Para desplegar los microservicios, se aplican los manifiestos Kubernetes:

```bash
kubectl apply -f micro1/Deployment.yaml
kubectl apply -f micro1/Service.yaml
kubectl apply -f micro1/Ingress.yaml

kubectl apply -f micro2/Deployment.yaml
kubectl apply -f micro2/Service.yaml
kubectl apply -f micro2/Ingress.yaml
```

### Configuración de variables de entorno

Se utilizan `ConfigMap` y `Secrets` para manejar variables sensibles y configuración, como las credenciales y URLs para DynamoDB y SQS, que se inyectan en los pods.

---

## 3. Integración con DynamoDB y SQS

### Creación de recursos

Desde la consola de AWS se crearon:

- Una tabla DynamoDB para almacenar órdenes y ventas.
- Una cola SQS para la comunicación entre microservicios.

### IAM Role for ServiceAccount (IRSA)

Para que los pods puedan acceder a DynamoDB y SQS, se configuró un IAM Role asociado a la ServiceAccount de Kubernetes mediante IRSA, usando el OIDC provider del cluster.

### Ejemplo de trust relationship para el role IAM:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B716D3041E"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B716D3041E:sub": "system:serviceaccount:default:microservice-sa"
        }
      }
    }
  ]
}
```

---

## 4. Configuración de Ingress y ALB

Se mantuvo la instalación del AWS Load Balancer Controller para exponer los servicios mediante un Application Load Balancer (ALB).

### Ejemplo de Ingress con rutas

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: microservices-ingress
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
spec:
  rules:
    - http:
        paths:
          - path: /orders
            pathType: Prefix
            backend:
              service:
                name: micro1-service
                port:
                  number: 80
          - path: /sales
            pathType: Prefix
            backend:
              service:
                name: micro2-service
                port:
                  number: 80
```

### Health checks

Se configuraron health checks en el ALB para verificar el estado de los pods y garantizar alta disponibilidad.

---

## 5. Pruebas con JMeter

Para validar el rendimiento del sistema, se configuró un Thread Group en JMeter para realizar 400 peticiones por minuto.

### Ejemplo de body JSON dinámico

```json
{
  "orderId": "${__threadNum}",
  "product": "Example Product",
  "quantity": 1
}
```

### Resultados clave obtenidos

- Latencia promedio: ~141 ms
- Porcentaje de errores: 0%
- Throughput: ~6.8 solicitudes por segundo

---

## 6. Evidencias y monitoreo

### Verificación de pods y logs

```bash
kubectl get pods
kubectl logs <pod-name>
```

### Evidencia en DynamoDB

Se verificó que se insertaron 407 registros en la tabla DynamoDB correspondiente.

### Métricas del VPC Endpoint de SQS

Se monitorearon métricas como bytes procesados para el VPC Endpoint de SQS, confirmando la correcta comunicación entre servicios.

---

## 7. Conclusiones

- No fue necesario implementar un API Gateway debido a la arquitectura basada en ALB y microservicios.
- La configuración de VPC Endpoints para DynamoDB y SQS mejoró la seguridad y latencia.
- EventBridge facilitó la integración y comunicación entre microservicios.
- El sistema soporta 400 peticiones por minuto sin necesidad de escalar a más de dos pods, demostrando eficiencia en la arquitectura.

---

# Experimento MediSupply 2

El propósito del Experimento 2 es validar la latencia base, la latencia bajo condiciones de estrés, el throughput y la consistencia eventual utilizando el microservicio de productos que consulta la tabla DynamoDB mirror. Este experimento busca asegurar que el sistema mantenga un rendimiento adecuado y una consistencia aceptable en escenarios de alta carga y replicación de datos.

Para ello, se incluyó el Microservicio 3 – Gestión de productos, creado específicamente para consultar información desde la tabla `medisupply-demo-mirror`. Este microservicio aprovecha la infraestructura ya desplegada en el Experimento 1 y permite validar escenarios de consistencia eventual en la replicación de datos entre tablas DynamoDB.

## Arquitectura Experimento 2



## Conclusiones Experimiento 2

- Validación de latencia base (ASR004, ASR005): Con 10 usuarios concurrentes, las métricas de JMeter confirmaron que el sistema mantuvo tiempos de respuesta inferiores a los umbrales definidos (P50 ≤ 300 ms, P95 ≤ 800 ms y P99 ≤ 1000 ms).
- Latencia bajo estrés (ASR004): En pruebas con 100 usuarios concurrentes, el sistema mantuvo un P95 por debajo de 1000 ms durante toda la ejecución, asegurando estabilidad bajo carga elevada.
- Consistencia eventual (ASR006): Se comprobó que el 99.9% de los productos fueron consultables en ≤1 s después de su inserción o actualización, confirmando el correcto funcionamiento de la tabla espejo en DynamoDB y el patrón de replicación adoptado.
- Disponibilidad (ASR003): Todas las pruebas reportaron una tasa de error menor al 0.1%, lo que valida la robustez de la arquitectura y el diseño distribuido de EKS con múltiples zonas de disponibilidad.
- Throughput (ASR006): Se alcanzó un rendimiento de más de 500 consultas por minuto por pod, demostrando que el sistema es eficiente y escalable en escenarios de alta concurrencia.