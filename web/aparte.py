import boto3
import time
import json
from flask import Flask  

REGION = 'us-east-1'

ec2 = boto3.client('ec2', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)  

app = Flask(__name__)  # Movido al inicio para mejor organización

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


def list_buckets_and_objects():
    result = []
    buckets = s3.list_buckets()
    for bucket in buckets['Buckets']:
        bucket_name = bucket['Name']
        bucket_data = {"nombre": bucket_name, "objetos": []}
        objects = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in objects:
            for obj in objects['Contents']:
                bucket_data["objetos"].append(obj['Key'])
        result.append(bucket_data)
    return result


def resource_report():
    ec2_info = []
    instances = ec2.describe_instances()
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            ec2_info.append({
                "id": instance['InstanceId'],
                "estado": instance['State']['Name'],
                "tipo": instance['InstanceType'],
                "ip_publica": instance.get('PublicIpAddress', 'No asignada')
            })
    return ec2_info


def listar_instancias():
    response = ec2.describe_instances()
    instancias = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instancias.append({
                "id": instance['InstanceId'],
                "estado": instance['State']['Name']
            })
    return instancias


@app.route("/")
def home():
    resultado = {
        "instancias_creadas": create_ec2_instances(),
        "s3_buckets": list_buckets_and_objects(),
        "reporte_ec2": resource_report(),
        "lista_instancias": listar_instancias()
    }
    return json.dumps(resultado, indent=2)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)  # Corregido el signo "=" faltante