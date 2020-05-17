from aws_cdk import core
import aws_cdk.aws_ec2 as ec2
from botocore.exceptions import ClientError
import boto3
import json
import ipaddress

#VPC informations
vpc_size="/16"
default_vpc_cidr_range="10.0.0.0"+vpc_size
max_vpc_cidr_range="10.255.0.0"+vpc_size
vpc_nb_ips=65536


class VPCPeeringConnection(ec2.CfnVPCPeeringConnection):
    def __init__(self,scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)
        

class CdkBlogVpcStack(core.Stack):

    def get_next_cidr_range(self,vpc_name,**kwargs):
        # The code that defines your stack goes here
        dynamodb = boto3.resource('dynamodb', region_name=kwargs['env'].region)

        # check if same vpc has been deployed once
        last_cidr_range_table = dynamodb.Table('last_cidr_range_table')

        try:
            response = last_cidr_range_table.get_item(
                Key={
                    "id": "last_cidr_range"
                }
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
            next_cidr_range=default_vpc_cidr_range
        else:
            item = response['Item']
            print("GetItem succeeded:")
            print(item)
            last_cidr_range=response['Item']['value']
            next_cidr_range=increment_cidr_range(last_cidr_range);

        cidr_range_table = dynamodb.Table('cidr_range_table')
        response_cidr_range_table = cidr_range_table.put_item(
           Item={
                'id': vpc_name,
                'vpc': next_cidr_range
            }
        )
        
        response_last_cidr_range_table = last_cidr_range_table.put_item(
           Item={
                'id': 'last_cidr_range',
                'value': next_cidr_range
            }
        )

        return next_cidr_range

    def __init__(self, scope: core.Construct, id: str, vpc_name:str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
            
        next_cidr_range = self.get_next_cidr_range(vpc_name,**kwargs)
        #Provisioning VPC
        self.vpc = ec2.Vpc(self, vpc_name,
            cidr=next_cidr_range,
            max_azs=3,

            subnet_configuration=[ec2.SubnetConfiguration(
                subnet_type=ec2.SubnetType.PUBLIC,
                name="Ingress",
                cidr_mask=24
            ), ec2.SubnetConfiguration(
                cidr_mask=24,
                name="Application",
                subnet_type=ec2.SubnetType.PRIVATE
            ), ec2.SubnetConfiguration(
                cidr_mask=28,
                name="Database",
                subnet_type=ec2.SubnetType.ISOLATED,
                reserved=True
            )
            ]
        )
        
        
class CdkBlogVpcPeeringStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, vpc:ec2.Vpc,peer_vpc:ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        vpc_peer=VPCPeeringConnection(self,'test', vpc_id=vpc.vpc_id, peer_vpc_id=peer_vpc.vpc_id)
        
        
def increment_cidr_range(current_cidr_range):
    startIp=current_cidr_range.split("/")[0]
    newip = ipaddress.IPv4Address(startIp)+vpc_nb_ips
    new_cidr_range=str(newip)+vpc_size
    #check if we used all available cidr_range
    if max_vpc_cidr_range == new_cidr_range:
        new_cidr_range=default_vpc_cidr_range
    return new_cidr_range
        