This is the CloudFormation template for self-managed worker node creation with Multus CNI plugin in self-managed ENI mode. This mode is useful when the application wants to have a full ownership for assigning and controlling the IP address to the Pod especially for secondary subnet that is usually exposed to the external network. In this case, default K8s network interface will be still under VPC CNI plugin's control while secondary subnet ENI will be controlled by the application (e.g. IP assignment by Pod or Helm definition). 

![image-20200424115637436](image-20200424115637436.jpg)

## Pre-requisite
This is applicable when the VPC CNI Plugin has the patch for Multus meta-CNI plugin support. 
﻿https://github.com/aws/amazon-vpc-cni-k8s/pull/866﻿

## Automation through CloudFormation

From the baseline CFN for self-managed node group, below functions are added;
- LifeCycle Hook Creation for the self-managed worker node group (NodeGroup).
- Lambda function creation for ENI attach for 2ndary subnet. 
- CloudWatch Event Rule to trigger Lambda function. 

**Note:** Before running this CloudFormation, you have to place lambda_function zip file (lambda_function.py) to your S3 bucket. 

Before running this CloudFormation, you have to place lambda_function zip file (lambda_function.py) to your S3 bucket. 

During CFN stack creation, 
* Select primary private subnet for the parameter of `Subets: The subnets where workers can be created.` 
* Select 2ndary (Multus) subnet for the parameter of `2ndSubnet: The subnet where multus 2ndary ENI will be connected to.`

After completion of stack creation, update aws-auth-cn.yaml with Node Role ARN in Output section of the CloudFormation result. 

**Terminate** all existing instances to make the Event rule and Lambda to be effective to new workers. 

If you use default EKS optimized AMI, since this package doesn't have netutils package, newly added ENI (eth1) doesn't get added to the kernel automatically. So, you have to login workernode and you have to try "sudo ifconfig eth up" once.  

## Extra note for the number of additioanl subnets

If workernode has to be attached with 2 additional subnets other than default k8s network, then `amazon-eks-nodegroup-2nd-2ENIs.yaml` CFN can be used. Current Lambda supports max 2 additional subnets attachment to the worker node group. 
