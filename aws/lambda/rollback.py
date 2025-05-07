import boto3
import json
import logging
from datetime import datetime

# Configuración ACTUALIZADA con tus datos
logger = logging.getLogger()
logger.setLevel(logging.INFO)
AWS_REGION = "us-east-1"  # Tu región AWS
S3_BUCKET = "avance-proyecto"  # Tu bucket S3

# Clientes de AWS configurados con tu región
ssm = boto3.client('ssm', region_name=AWS_REGION)
s3 = boto3.client('s3', region_name=AWS_REGION)
cloudwatch = boto3.client('cloudwatch', region_name=AWS_REGION)

def lambda_handler(event, context):
    try:
        app_name = event['appName']
        app_version = event['appVersion']
        reason = event['reason']
        instances = event['instances']
        
        logger.info(f"Iniciando rollback para {app_name} v{app_version}. Motivo: {reason}")
        
        # 1. Obtener versión anterior
        previous_version = get_previous_version(app_name, app_version)
        if not previous_version:
            raise Exception("No se encontró versión anterior para rollback")
        
        # 2. Ejecutar rollback en instancias
        rollback_commands = execute_rollback(app_name, previous_version, instances)
        
        # 3. Verificar resultados
        failed_instances = verify_rollback(rollback_commands)
        
        # 4. Registrar métricas
        log_metrics(app_name, app_version, previous_version, len(instances), len(failed_instances))
        
        if failed_instances:
            return {
                'statusCode': 206,
                'body': f"Rollback completado con errores en instancias: {failed_instances}"
            }
        return {
            'statusCode': 200,
            'body': "Rollback completado con éxito"
        }
        
    except Exception as e:
        logger.error(f"Error en rollback: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error durante rollback: {str(e)}"
        }

def get_previous_version(app_name, current_version):
    try:
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET,  # Usa tu bucket actualizado
            Prefix=f"{app_name}/",
            Delimiter="/"
        )
        versions = [p['Prefix'].split('/')[1] for p in response.get('CommonPrefixes', [])]
        return next((v for v in sorted(versions, reverse=True) if v != current_version), None)
    except Exception as e:
        logger.error(f"Error obteniendo versión anterior: {str(e)}")
        return None

def execute_rollback(app_name, version, instances):
    commands = []
    for i in range(0, len(instances), 10):  # Lotes de 10 instancias
        batch = instances[i:i+10]
        response = ssm.send_command(
            InstanceIds=batch,
            DocumentName="AWS-RunShellScript",
            Parameters={
                'commands': [
                    f"rm -rf /opt/{app_name}",
                    f"aws s3 cp s3://{S3_BUCKET}/{app_name}/{version}/app.zip /tmp/{app_name}.zip",  # Bucket actualizado
                    f"unzip /tmp/{app_name}.zip -d /opt/{app_name}",
                    f"chmod +x /opt/{app_name}/start.sh",
                    f"/opt/{app_name}/start.sh"
                ]
            },
            TimeoutSeconds=300
        )
        commands.append(response['Command']['CommandId'])
    return commands

def verify_rollback(command_ids):
    failed = []
    for cmd_id in command_ids:
        invocations = ssm.list_command_invocations(CommandId=cmd_id, Details=True)
        for inv in invocations['CommandInvocations']:
            if inv['Status'] != 'Success':
                failed.append(inv['InstanceId'])
    return failed

def log_metrics(app_name, failed_ver, rollback_ver, total_instances, failed_instances):
    cloudwatch.put_metric_data(
        Namespace="DeploymentMetrics",
        MetricData=[{
            'MetricName': 'RollbackExecuted',
            'Dimensions': [
                {'Name': 'Application', 'Value': app_name},
                {'Name': 'FailedVersion', 'Value': failed_ver},
                {'Name': 'RollbackVersion', 'Value': rollback_ver}
            ],
            'Value': 1,
            'Unit': 'Count'
        }]
    )