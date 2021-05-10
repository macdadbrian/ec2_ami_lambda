import boto3
import datetime
import time
import random
import copy
import os
import re

def lambda_handler(event, context):

    today = datetime.date.today()
    today_string = time.strftime('%Y-%m-%d.%H%M%S')

    ec2_client = boto3.client('ec2','eu-west-1')
    ec2_resource = boto3.resource('ec2','eu-west-1')

    result = ec2_client.describe_instances(
            Filters = [ {'Name': 'tag:celltrak_ec2_ami', 'Values': ['true']}
             ]
        )

    instances = result['Reservations']

    instance_ids=[]

    for instance in instances:
        instance_ids.append(instance['Instances'][0]['InstanceId'])
    

    for i in instance_ids:
        print(i)
    
        ec2_resource = boto3.resource('ec2','us-east-1')
    
        ec2instance = ec2_resource.Instance(i)
    
        for tags in ec2instance.tags:
            if tags["Key"] == 'Name':
                instancename = tags["Value"]
    
        print(instancename)
    
        image = ec2_client.create_image(
            InstanceId=i,
            Name=instancename +" "+ today_string,
            Description=instancename +" "+ today_string,
            NoReboot=True,
            DryRun=False)
    
    
        image_resource = ec2_resource.Image(
                                   image['ImageId'])
    
    
        image_resource.create_tags(Tags=[ { 'Key': 'Name', 'Value': instancename +' '+ today_string },
                                      { 'Key': 'Cost Center', 'Value': 'V2' },
                                      { 'Key': 'CreatedOn', 'Value': today_string },
                                      { 'Key': 'Use', 'Value': 'Lambda_AMI_EC2_Snapshot'}
                                    ])

        time.sleep( 20 )
    
  
        block_devices = copy.deepcopy(image_resource.block_device_mappings)
        print (block_devices)

        for snap in block_devices:
            if not 'Ebs' in snap:
                continue
            snapshot_id = snap['Ebs']['SnapshotId']
            print (snapshot_id)
            snapshot = ec2_resource.Snapshot(snapshot_id)
            print (snapshot)
    
            ec2_client.create_tags(Resources=[snapshot_id,],Tags=[ { 'Key': 'Name', 'Value': instancename +' '+ today_string },                      
                                      { 'Key': 'Cost Center', 'Value': 'V2' },
                                      { 'Key': 'CreatedOn', 'Value': today_string },                       
                                      { 'Key': 'Use', 'Value': 'Lambda_AMI_EC2_Snapshot' }                                
                                    ])
    
        ami_image_list = []
    
        ami_image_name = list(map(lambda i: i['Name'], ec2_client.describe_images(
            Filters = [ {'Name' : 'tag:Name', 'Values' : [ instancename +'*' ]},
          ] 
            )['Images']))
    
        def atoi(text):
            return int(text) if text.isdigit() else text

        def natural_keys(text):
            return [ atoi(c) for c in re.split(r'(\d+)', text) ]
    

        for ami in ami_image_name:
            ami_image_list.append(ami)
        print (ami_image_list)

        ami_image_list.sort(key=natural_keys) 

        if len(ami_image_list) > 3:
            result = [ ami_image_list[0] ]
            result_image = (' ' .join(result))
            print (result_image)
        
    
            result_ami_name = list(map(lambda i: i['ImageId'], ec2_client.describe_images(
                Filters=[
                         {
                           'Name' : 'tag:Name',
                           'Values' : [ result_image ]
                         },
               ] 
                 )['Images']))
    
            celltrak_ami_purge = (' ' .join(result_ami_name))
    
            print (celltrak_ami_purge)

            celltrak_deregister_ami = ec2_client.deregister_image(
                ImageId=celltrak_ami_purge,
                DryRun=False)
    
            print (celltrak_deregister_ami)
    
            celltrak_ami_snapshots = ec2_client.describe_snapshots(Filters=[{'Name': 'tag:Name', 'Values': [ result_image ]}])
    
            for snapshot in celltrak_ami_snapshots['Snapshots']:
                delete_snapshots = (snapshot['SnapshotId'])
                print (delete_snapshots)
            
                delete = ec2_client.delete_snapshot(
                                                       SnapshotId=delete_snapshots,
                                                       DryRun=False)
            
                print (delete)
