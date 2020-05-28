import boto3, json, sys, requests
from requests.packages.urllib3 import Retry

ec2_client = boto3.client('ec2', region_name='us-west-2')
ipv6_addr = "2600:1f13:488:4999::20"
#ipv6_addr = "2600:1f13:488:4999::100"
subnetv6_cidr = "2600:1f13:488:4999::/64"

def reassign_ipv6():
    release_ipv6()
    assign_ipv6()

def release_ipv6():
    response = ec2_client.describe_network_interfaces(
        Filters=[
            {
                'Name': 'ipv6-addresses.ipv6-address',
                'Values': [
                    ipv6_addr,
                ]
            },
        ],
    )
    if response['NetworkInterfaces'] == []:
        print("ENI of ipv6 not attached yet, no need to release")
    else:
        for j in response['NetworkInterfaces']:
            network_interface_id = j['NetworkInterfaceId']
            break
        response = ec2_client.unassign_ipv6_addresses(
            Ipv6Addresses=[
                ipv6_addr,
            ],
            NetworkInterfaceId = network_interface_id
        )

def assign_ipv6():
    instance_id = get_instance_id()
    response = ec2_client.describe_subnets(
        Filters=[
            {
                'Name': 'ipv6-cidr-block-association.ipv6-cidr-block',
                'Values': [
                    subnetv6_cidr,
                ]
            },
        ]
    )

    for i in response['Subnets']:
        subnet_id = i['SubnetId']
        break

    response = ec2_client.describe_network_interfaces(
        Filters=[
            {
                'Name': 'subnet-id',
                'Values': [
                    subnet_id,
                ]
            },
            {
                'Name': 'attachment.instance-id',
                'Values': [
                    instance_id,
                ]
            }
        ]
    )

    for j in response['NetworkInterfaces']:
        network_interface_id = j['NetworkInterfaceId']
        break


    response = ec2_client.assign_ipv6_addresses(
        Ipv6Addresses=[
            ipv6_addr,
        ],
        NetworkInterfaceId=network_interface_id
    )

def get_instance_id():
    instance_identity_url = "http://169.254.169.254/latest/dynamic/instance-identity/document"
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.3)
    metadata_adapter = requests.adapters.HTTPAdapter(max_retries=retries)
    session.mount("http://169.254.169.254/", metadata_adapter)
    try:
        r = requests.get(instance_identity_url, timeout=(2, 5))
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as err:
        print("Connection to AWS EC2 Metadata timed out: " + str(err.__class__.__name__))
        print("Is this an EC2 instance? Is the AWS metadata endpoint blocked? (http://169.254.169.254/)")
        sys.exit(1)
    response_json = r.json()
    instanceid = response_json.get("instanceId")
    return(instanceid)

reassign_ipv6()
