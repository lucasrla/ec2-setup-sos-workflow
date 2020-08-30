import pathlib

import boto3


def launch_instance(cfg):
    client = boto3.client("ec2")
    ec2 = boto3.resource("ec2")

    ami_id = cfg["ec2"]["ami_id"]
    inst_type = cfg["ec2"]["instance_type"]
    iam_profile = cfg["ec2"]["iam_profile"]
    security_group_id = cfg["ec2"]["security_group_id"]

    fname_stem = cfg["project_name"]
    inst_tag = f"{fname_stem}"

    pem_path = cfg["hosts"]["ec2"]["pem_file"]
    key_name = pathlib.Path(pem_path).stem

    instance = {}

    _ = client.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [inst_tag]},
            {"Name": "instance-state-code", "Values": ["16"]},
        ]
    )

    n_instances = len(_["Reservations"])
    print(f"{n_instances} running ec2_instance(s) tagged as '{inst_tag}'")

    if n_instances == 0:
        client.run_instances(
            ImageId=ami_id,
            InstanceType=inst_type,
            SecurityGroupIds=[security_group_id],
            IamInstanceProfile={"Name": iam_profile},
            KeyName=key_name,
            MaxCount=1,
            MinCount=1,
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": inst_tag}],
                }
            ],
        )

    for k in client.describe_instances()["Reservations"]:
        for i in k["Instances"]:
            # print(f"{i['InstanceId']}")

            if i["State"]["Code"] > 16:
                continue

            if "Tags" in i.keys():
                tag = i["Tags"][0]["Value"]
                if tag != inst_tag:
                    continue

                instance["id"] = i["InstanceId"]
                instance["tag"] = tag

    inst = ec2.Instance(instance["id"])

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Instance.state
    if inst.state["Code"] == 0 or inst.state["Code"] == 16:
        inst.wait_until_running()

        inst.reload()
        instance["public_dns_name"] = inst.public_dns_name
        instance["public_ip"] = inst.public_ip_address
        instance["availability_zone"] = inst.placement["AvailabilityZone"]

    instance["state"] = inst.state["Name"]

    print(f"ec2_instance: {instance}")

    return instance


def wait_for_status_checks(instance):
    # TODO: waiting for status checks might not be necessary
    # https://stackoverflow.com/a/48795544

    client = boto3.client("ec2")
    waiter_conf = {"Delay": 20, "MaxAttempts": 30}

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Waiter.InstanceStatusOk
    client.get_waiter("instance_status_ok").wait(
        InstanceIds=[instance["id"]], WaiterConfig=waiter_conf
    )

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Waiter.SystemStatusOk
    client.get_waiter("system_status_ok").wait(
        InstanceIds=[instance["id"]], WaiterConfig=waiter_conf
    )


def terminate_instance(instance):
    client = boto3.client("ec2")

    inst_id = instance["id"]
    inst_tag = instance["tag"]

    r = client.delete_tags(
        Resources=[inst_id], Tags=[{"Key": "Name", "Value": inst_tag}]
    )
    # print(r)

    resp = client.terminate_instances(InstanceIds=[inst_id])
    # print(resp)

    return resp["TerminatingInstances"][0]["CurrentState"]["Name"]