import boto3
import botocore
import os
from datetime import datetime

ec2_client = boto3.client('ec2')
asg_client = boto3.client('autoscaling')
ec2 = boto3.resource('ec2')


def lambda_handler(event, context):
    if event["detail-type"] == "EC2 Instance-launch Lifecycle Action":
        instance_id = event['detail']['EC2InstanceId']
        LifecycleHookName=event['detail']['LifecycleHookName']
        AutoScalingGroupName=event['detail']['AutoScalingGroupName']
        Index = 1
        subnetid1 = os.environ['SubnetId']
        subnetid2 = os.environ['SubnetId2']
        interface_id = create_interface(subnetid1)
        attachment = attach_interface(interface_id,instance_id,Index)
        if subnetid2 == 'None':
            interface_id2=True
            attachment2=True
        else:
            Index = Index+1
            interface_id2 = create_interface(subnetid2)
            attachment2 = attach_interface(interface_id2,instance_id,Index)

        if not interface_id or not interface_id2:
            complete_lifecycle_action_failure(LifecycleHookName,AutoScalingGroupName,instance_id)
        elif not attachment or not attachment2:
            complete_lifecycle_action_failure(LifecycleHookName,AutoScalingGroupName,instance_id)
            delete_interface(interface_id)
        else:
            complete_lifecycle_action_success(LifecycleHookName,AutoScalingGroupName,instance_id)


def get_subnet_id(instance_id):
    try:
        result = ec2_client.describe_instances(InstanceIds=[instance_id])
        vpc_subnet_id = result['Reservations'][0]['Instances'][0]['SubnetId']
        log("Subnet id: {}".format(vpc_subnet_id))

    except botocore.exceptions.ClientError as e:
        log("Error describing the instance {}: {}".format(instance_id,\
        e.response['Error']))
        vpc_subnet_id = None
    return vpc_subnet_id


def create_interface(subnet_id):
    network_interface_id = None
    if subnet_id:
        try:
            network_interface = ec2_client.create_network_interface(SubnetId=subnet_id)
            network_interface_id = network_interface['NetworkInterface']['NetworkInterfaceId']
            log("Created network interface: {}".format(network_interface_id))
        except botocore.exceptions.ClientError as e:
            log("Error creating network interface: {}".format(e.response['Error']))
    return network_interface_id


def attach_interface(network_interface_id, instance_id, index):
    attachment = None
    if network_interface_id and instance_id:
        try:
            attach_interface = ec2_client.attach_network_interface(
                NetworkInterfaceId=network_interface_id,
                InstanceId=instance_id,
                DeviceIndex=index
            )
            attachment = attach_interface['AttachmentId']
            log("Created network attachment: {}".format(attachment))
        except botocore.exceptions.ClientError as e:
            log("Error attaching network interface: {}".format(e.response['Error']))

    network_interface = ec2.NetworkInterface(network_interface_id)
    network_interface.create_tags(
        Tags=[
                {
                    'Key': 'node.k8s.amazonaws.com/no_manage',
                    'Value': 'true'
            }
        ]
    )
    return attachment


def delete_interface(network_interface_id):
    try:
        ec2_client.delete_network_interface(
            NetworkInterfaceId=network_interface_id
        )
        log("Deleted network interface: {}".format(network_interface_id))
        return True

    except botocore.exceptions.ClientError as e:
        log("Error deleting interface {}: {}".format(network_interface_id,e.response['Error']))


def complete_lifecycle_action_success(hookname,groupname,instance_id):
    try:
        asg_client.complete_lifecycle_action(
            LifecycleHookName=hookname,
            AutoScalingGroupName=groupname,
            InstanceId=instance_id,
            LifecycleActionResult='CONTINUE'
        )
        log("Lifecycle hook CONTINUEd for: {}".format(instance_id))
    except botocore.exceptions.ClientError as e:
            log("Error completing life cycle hook for instance {}: {}".format(instance_id, e.response['Error']))
            log('{"Error": "1"}')

def complete_lifecycle_action_failure(hookname,groupname,instance_id):
    try:
        asg_client.complete_lifecycle_action(
            LifecycleHookName=hookname,
            AutoScalingGroupName=groupname,
            InstanceId=instance_id,
            LifecycleActionResult='ABANDON'
        )
        log("Lifecycle hook ABANDONed for: {}".format(instance_id))
    except botocore.exceptions.ClientError as e:
            log("Error completing life cycle hook for instance {}: {}".format(instance_id, e.response['Error']))
            log('{"Error": "1"}')

def log(error):
    print('{}Z {}'.format(datetime.utcnow().isoformat(), error))
