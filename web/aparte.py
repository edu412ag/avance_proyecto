import boto3
import time


REGION = 'us-east-1'  


ec2 = boto3.client('ec2', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')



def create_ec2_instances():
    print("Creando instancias EC2...")
    response = ec2.run_instances(
        ImageId='ami-0c55b159cbfafe1f0',  # Amazon Linux 2 AMI - cambia según tu región
        InstanceType='t2.micro',
        MinCount=1,
        MaxCount=2,
        KeyName='eduvockey',  # Pon el nombre de tu Key Pair
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Purpose', 'Value': 'LearnerLab'}]
            },
        ]
    )
    instance_ids = [instance['InstanceId'] for instance in response['Instances']]
    print(f"Instancias creadas: {instance_ids}")
    return instance_ids




def listar_instancias():
    response = ec2.describe_instances()
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            print(f"ID: {instance['InstanceId']}, Estado: {instance['State']['Name']}")

def resource_report():
    print("\n--- Reporte de Recursos EC2 ---")
    instances = ec2.describe_instances()
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            print(f"ID: {instance['InstanceId']}")
            print(f"Estado: {instance['State']['Name']}")
            print(f"Tipo: {instance['InstanceType']}")
            print(f"IP Pública: {instance.get('PublicIpAddress', 'No asignada')}")
            print("-" * 30)

# =======================
# 3. Listar Buckets y Objetos S3
# =======================

def list_buckets_and_objects():
    print("\n--- Buckets y Objetos en S3 ---")
    buckets = s3.list_buckets()


    import pdb; pdb.set_trace()

    for bucket in buckets['Buckets']:
        print(f"Bucket: {bucket['Name']}")
        objects = s3.list_objects_v2(Bucket=bucket['Name'])
        if 'Contents' in objects:
            for obj in objects['Contents']:
                print(f"  - {obj['Key']}")
        else:
            print("  (Vacío)")
        print("-" * 30)


if __name__ == "__main__":
    
    instance_ids = create_ec2_instances()

    print ("listado de buckets S3:")
    list_buckets_and_objects()
    print("Reporte de Recursos:")
    resource_report()
    print("Lista de instancias:")
    listar_instancias()
