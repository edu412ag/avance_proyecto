import boto3
from flask import Flask, jsonify
import logging
from functools import wraps

# Configuración básica
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes
REGION = 'us-east-1'
CONFIG = {
    'ec2': {
        'ImageId': 'ami-0e449927258d45bc4',
        'InstanceType': 't2.micro',
        'KeyName': 'equipo5avance',
        'TagSpecifications': [{
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Purpose', 'Value': 'LearnerLab'}]
        }]
    }
}

# Inicialización de clientes AWS
try:
    ec2 = boto3.client('ec2', region_name=REGION)
    s3 = boto3.client('s3', region_name=REGION)
except Exception as e:
    logger.error(f"Error inicializando clientes AWS: {str(e)}")
    raise

# Decorador para manejo de errores
def handle_aws_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ec2.exceptions.ClientError as e:
            logger.error(f"Error AWS EC2: {str(e)}")
            return jsonify({"error": str(e)}), 500
        except s3.exceptions.ClientError as e:
            logger.error(f"Error AWS S3: {str(e)}")
            return jsonify({"error": str(e)}), 500
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500
    return wrapper


def create_ec2_instances():
    response = ec2.run_instances(
        ImageId='ami-0e449927258d45bc4',
        InstanceType='t2.micro',
        MinCount=1,




        MaxCount=2,




        KeyName='equipo5avance',  # Pon el nombre de tu Key Pair


        
 
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Purpose', 'Value': 'LearnerLab'}]
            },
        ]
    )
    instance_ids = [instance['InstanceId'] for instance in response['Instances']]
    return instance_ids

# Endpoints
@app.route("/")
def health_check():
    return jsonify({"status": "healthy", "service": "AWS Manager API"})


@app.route("/instances", methods=['GET'])
@handle_aws_errors
def get_instances():
    """Obtiene todas las instancias EC2"""
    response = ec2.describe_instances()
    instances = []
    
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instances.append({
                "id": instance['InstanceId'],
                "state": instance['State']['Name'],
                "type": instance['InstanceType'],
                "public_ip": instance.get('PublicIpAddress', 'N/A')
            })
    
    return jsonify({"instances": instances})

@app.route("/instance", methods=['POST'])
@handle_aws_errors
def create_instance():
    """Crea una nueva instancia EC2"""
    response = ec2.run_instances(
        ImageId=CONFIG['ec2']['ImageId'],
        InstanceType=CONFIG['ec2']['InstanceType'],
        MinCount=1,
        MaxCount=1,
        KeyName=CONFIG['ec2']['KeyName'],
        TagSpecifications=CONFIG['ec2']['TagSpecifications']
    )
    
    instance_id = response['Instances'][0]['InstanceId']
    logger.info(f"Instancia creada: {instance_id}")
    
    return jsonify({
        "message": "Instance created successfully",
        "instance_id": instance_id
    }), 201

@app.route("/buckets", methods=['GET'])
@handle_aws_errors
def get_buckets():
    """Lista todos los buckets S3 con sus objetos"""
    buckets = s3.list_buckets()
    result = []
    
    for bucket in buckets['Buckets']:
        bucket_name = bucket['Name']
        objects = []
        
        try:
            contents = s3.list_objects_v2(Bucket=bucket_name).get('Contents', [])
            objects = [obj['Key'] for obj in contents]
        except Exception as e:
            logger.warning(f"No se pudieron listar objetos en {bucket_name}: {str(e)}")
        
        result.append({
            "name": bucket_name,
            "objects": objects
        })
    
    return jsonify({"buckets": result})

# Configuración de producción
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)