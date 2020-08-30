# ec2-setup-sos-workflow

A simple pipeline built with [SoS Workflow](https://vatlab.github.io/sos-docs/workflow.html) ([GitHub repository](https://github.com/vatlab/sos)) to manage [AWS EC2 instances and EBS volumes](https://aws.amazon.com/ec2/).

## Installation

### conda

```sh
conda create --name ec2-setup-sos --channel conda-forge python=3 pyyaml boto3 sos black
git clone https://github.com/lucasrla/ec2-setup-sos-workflow
cd ec2-setup-sos-workflow
conda activate ec2-setup-sos
```

### poetry or pip

```sh
git clone https://github.com/lucasrla/ec2-setup-sos-workflow
cd ec2-setup-sos-workflow

# create and activate a virtualenv, for example:
pyenv virtualenv ec2-setup-sos && pyenv local ec2-setup-sos

# install the dependencies, either with:
poetry install
# or:
pip install -r requirements.txt

# note, requirements.txt was generated via:
# poetry export --without-hashes -f requirements.txt -o requirements.txt
```

## Configuration

```sh
# edit config.template.yml to match your needs
vim config.template.yml
# and then save it as config.yml

# make sure your ~/.aws/config is properly set
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html
cat ~/.aws/config

# make sure the [default] is correct within ~/.aws/credentials
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
cat ~/.aws/credentials
```

## Usage

### Init

To launch a new EC2 setup:

```sh
sos run -c config.yml init.sos -v4

# this will:
# launch a new ec2 instance, create a new ebs volume, attach the volume to the instance, 
# add the instance's public dns/ip to your local ssh known_hosts, update the yum packages,
# install conda and sos, and format the ebs volume and mount it to the instance
```

After running `init.sos` above, a new instance is now ready for use.

### Your pipeline/workflow

If you are using SoS workflows, set `metadata/config_with_ec2_host.yml` as your config file when running tasks within the instance. For example: `sos run -c metadata/config_with_ec2_host.yml YOUR_WORKFLOW.sos`

### Teardown

When done with your pipeline:

```sh
sos run -c config.yml teardown.sos -v4

# this will undo the steps done with `init.sos`:
# umount the ebs volume (device), detach it, terminate the instance, delete metadata files,
# optionally save a snapshot of the ebs volume, and delete the volume

```

After running `teardown.sos`, all your EC2 resrouces are not deleted/terminated (except for the snapshot of your EBS volume, if you have chosen to create it).


## Troubleshooting

```sh
# lists all local tasks
# tasks live in ~/.sos/tasks/
sos status

# check the details of a specific task/job
# -v4 (max verbosity level) is great for debugging
sos status TASK_HASH_ID -v4

# for example:
sos status c23ad54f11df17b6
    c23ad54f11df17b6	5214df0f1e51390c ebs_umount ec2-setup-sos-workflow	Ran for 0s    	failed

sos status c23ad54f11df17b6 -v4
    ...


# check the connection to the ec2 instance
# which is also named ec2 in our config YAML
sos remote -c metadata/config_with_ec2_host.yml test ec2 -v4
```

## License

This is [Free Software](https://www.gnu.org/philosophy/free-sw.html) distributed under the [GNU General Public License v3.0](https://choosealicense.com/licenses/gpl-3.0/).