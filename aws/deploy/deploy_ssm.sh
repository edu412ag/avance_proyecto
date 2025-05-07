#!/bin/bash
# Script COMPLETO de despliegue con AWS SSM - CONFIGURADO PARA TU ENTORNO

# Configuración ESPECÍFICA PARA TU PROYECTO
APP_NAME="mi-aplicacion"
APP_VERSION="1.0.0"
S3_BUCKET="avance-proyecto"
S3_KEY="${APP_NAME}/${APP_VERSION}/app.zip"
SSM_DOCUMENT_NAME="AWS-RunShellScript"
INSTANCE_IDS=("i-0af43ba679fcca4fd")  # Tu Instance ID
MAX_CONCURRENT=1                      # Como solo tienes 1 instancia
AWS_REGION="us-east-1"                # Tu región

# Configura la región por defecto para AWS CLI
export AWS_DEFAULT_REGION=$AWS_REGION

# Descargar paquete desde S3
download_package() {
  local instance_id=$1
  aws ssm send-command \
    --instance-ids "$instance_id" \
    --document-name "$SSM_DOCUMENT_NAME" \
    --parameters '{"commands":[
      "mkdir -p /tmp/'${APP_NAME}',
      "aws s3 cp s3://'${S3_BUCKET}'/'${S3_KEY}' /tmp/'${APP_NAME}'/app.zip"
    ]}' \
    --output-s3-bucket-name "$S3_BUCKET" \
    --output-s3-key-prefix "ssm-output/${APP_NAME}/download" \
    --query "Command.CommandId" \
    --output text
}

# Desplegar aplicación
deploy_application() {
  local instance_id=$1
  aws ssm send-command \
    --instance-ids "$instance_id" \
    --document-name "$SSM_DOCUMENT_NAME" \
    --parameters '{"commands":[
      "unzip -o /tmp/'${APP_NAME}'/app.zip -d /opt/'${APP_NAME}'",
      "chmod +x /opt/'${APP_NAME}'/start.sh",
      "/opt/'${APP_NAME}'/start.sh"
    ]}' \
    --output-s3-bucket-name "$S3_BUCKET" \
    --output-s3-key-prefix "ssm-output/${APP_NAME}/deploy" \
    --query "Command.CommandId" \
    --output text
}

# Verificar estado
check_deployment_status() {
  local command_id=$1
  local instance_id=$2
  aws ssm get-command-invocation \
    --command-id "$command_id" \
    --instance-id "$instance_id" \
    --query "Status" \
    --output text
}

# Lógica de despliegue por lotes (adaptada para 1 instancia)
batch_deploy() {
  declare -A commands
  declare -A deploy_commands

  echo "=== Fase 1: Descarga del paquete ==="
  for instance_id in "${INSTANCE_IDS[@]}"; do
    echo "Descargando en $instance_id..."
    commands["$instance_id"]=$(download_package "$instance_id")
  done

  echo "=== Verificando descargas ==="
  for instance_id in "${!commands[@]}"; do
    while :; do
      status=$(check_deployment_status "${commands[$instance_id]}" "$instance_id")
      [[ "$status" == "Success" ]] && break
      [[ "$status" == "Failed" ]] && { trigger_rollback "Download failed"; exit 1; }
      sleep 5
    done
  done

  echo "=== Fase 2: Despliegue ==="
  for instance_id in "${INSTANCE_IDS[@]}"; do
    echo "Desplegando en $instance_id..."
    deploy_commands["$instance_id"]=$(deploy_application "$instance_id")
  done

  echo "=== Verificando despliegues ==="
  for instance_id in "${!deploy_commands[@]}"; do
    status=$(check_deployment_status "${deploy_commands[$instance_id]}" "$instance_id")
    [[ "$status" != "Success" ]] && { trigger_rollback "Deploy failed"; exit 1; }
  done
}

# Rollback automático
trigger_rollback() {
  local reason="$1"
  echo "🚨 ERROR: $reason - Activando rollback..."
  aws lambda invoke \
    --function-name "DeploymentRollback" \
    --payload '{
      "reason": "'"$reason"'",
      "appName": "'"$APP_NAME"'",
      "appVersion": "'"$APP_VERSION"'",
      "instances": '"$(printf '%s\n' "${INSTANCE_IDS[@]}" | jq -R . | jq -s .)"'
    }' \
    rollback.log
  exit 1
}

# --- Ejecución principal ---
batch_deploy
echo "✅ Despliegue completado en la instancia ${INSTANCE_IDS[0]}"