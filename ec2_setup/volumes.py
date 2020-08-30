import math
import string

import boto3


def create_volume(cfg, instance):
    client = boto3.client("ec2")
    s3 = boto3.resource("s3")

    fname_stem = cfg["project_name"]
    vol_tag = f"{fname_stem}-VOL"

    if "ebs" in cfg.keys() and "s3_bucket_input" in cfg["ebs"].keys():
        s3_bucket = cfg["ebs"]["s3_bucket_input"]

        bucket = s3.Bucket(s3_bucket)
        total_size = 0
        for k in bucket.objects.all():
            total_size += k.size

        if "s3_bucket_size_multiplier" in cfg["ebs"].keys():
            multiplier = int(cfg["ebs"]["s3_bucket_size_multiplier"])
        else:
            multiplier = 1

        vol_size = math.ceil(total_size / (10 ** 9)) * multiplier

    elif "ebs" in cfg.keys() and "volume_size" in cfg["ebs"].keys():
        vol_size = int(cfg["ebs"]["volume_size"])

    else:
        # 100 GB is our default for volume size
        vol_size = 100

    volume = {}

    for v in client.describe_volumes()["Volumes"]:
        # print(v)

        if v["State"] != "available":
            continue

        if "Tags" in v.keys():
            tag = v["Tags"][0]["Value"]
            if tag != vol_tag:
                continue

            volume["id"] = v["VolumeId"]
            volume["availability_zone"] = v["AvailabilityZone"]
            volume["size"] = v["Size"]
            volume["tag"] = tag

    if not volume:
        r = client.create_volume(
            AvailabilityZone=instance["availability_zone"],
            TagSpecifications=[
                {"ResourceType": "volume", "Tags": [{"Key": "Name", "Value": vol_tag}]}
            ],
            Size=vol_size,
        )

        volume["id"] = r["VolumeId"]
        volume["availability_zone"] = r["AvailabilityZone"]
        volume["size"] = r["Size"]
        volume["tag"] = vol_tag

    print(f"ebs_volume: {volume}")

    return volume


def get_free_device_name(instance):
    # https://stackoverflow.com/questions/32844854/boto3-show-next-available-device-name-on-instance
    all_device_names = ["/dev/xvd%s" % (x) for x in string.ascii_lowercase]
    device_list = instance.block_device_mappings
    used_device_names = set()
    for device in device_list:
        used_device_names.add(device["DeviceName"])
    return list(set(all_device_names) - used_device_names).pop()


def attach_volume(volume, instance):
    ec2 = boto3.resource("ec2")
    client = boto3.client("ec2")

    inst = ec2.Instance(instance["id"])
    # inst.block_device_mappings

    device = get_free_device_name(inst)

    # https://stackoverflow.com/questions/44807023/how-to-verify-volume-successfully-created-attached-in-boto3
    if ec2.Volume(volume["id"]).state != "in-use":
        client.get_waiter("volume_available").wait(VolumeIds=[volume["id"]])

    if len(ec2.Volume(volume["id"]).attachments) == 0:
        client.attach_volume(
            Device=device,
            InstanceId=instance["id"],
            VolumeId=volume["id"],
        )

    print("ebs_volume attachments:", ec2.Volume(volume["id"]).attachments)
    print("ec2_instance device:", device)

    return device


def detach_volume(volume):
    ec2 = boto3.resource("ec2")
    client = boto3.client("ec2")

    if (
        ec2.Volume(volume["id"]).state == "in-use"
        or len(ec2.Volume(volume["id"]).attachments) > 0
    ):
        client.detach_volume(VolumeId=volume["id"])
        client.get_waiter("volume_available").wait(VolumeIds=[volume["id"]])


def create_snapshot(volume):
    client = boto3.client("ec2")

    resp = client.create_snapshot(
        VolumeId=volume["id"],
        Description=volume["tag"] + "-latest",
        TagSpecifications=[
            {
                "ResourceType": "snapshot",
                "Tags": [{"Key": "Name", "Value": volume["tag"]}],
            }
        ],
    )

    # beware! snapshots can take hours to create (depending on their size)
    # why wait? because it is not clear if deleting the volume before the snapshot is done will affect the data
    # https://serverfault.com/questions/803995/deleted-the-data-while-amazon-ebs-volume-while-snapshot-in-pending#comment1025541_803996
    # https://www.reddit.com/r/aws/comments/hmh100/ebs_volume_delete_and_snapshot/
    # TODO: sort this out (i.e. test it myself!)
    client.get_waiter("snapshot_completed").wait(
        SnapshotIds=[resp["SnapshotId"]], WaiterConfig={"Delay": 60, "MaxAttempts": 300}
    )

    snapshot = {"id": resp["SnapshotId"]}
    print("ebs_snapshot:", snapshot)

    return snapshot


def delete_volume(volume):
    client = boto3.client("ec2")
    client.delete_volume(VolumeId=volume["id"])