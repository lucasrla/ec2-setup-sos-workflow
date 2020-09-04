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

# note, requirements.txt in this repository were generated via:
# poetry export --without-hashes -f requirements.txt -o requirements.txt
```


## Configuration

```sh
# edit config.TEMPLATE.yml to match your needs
vim config.TEMPLATE.yml
# and then save it as config.yml

# edit hosts.TEMPLATE.yml to match your needs
vim hosts.TEMPLATE.yml
# save it as ~/.sos/hosts.yml

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
# install conda and sos, format the ebs volume, and mount it to the instance
```

After running `init.sos`, a new instance will be ready for use.

### Your pipeline/workflow

If you are using SoS workflows, you can now run tasks within the instance via `tasks: queue='ec2'`.

### Teardown

When done with your pipeline:

```sh
sos run -c config.yml teardown.sos -v4

# this will undo the steps done with `init.sos`:
# umount the ebs volume (device), detach it, terminate the instance, delete metadata files,
# optionally save a snapshot of the ebs volume, and delete the volume
```

After running `teardown.sos`, the EC2 resources created with `init.sos` will be deleted/terminated (except for the snapshot of your EBS volume, if you have chosen to create it).


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
sos remote test ec2 -v4


# if substeps are being skipped because of saved signatures
# remove these signatures with:
sos remove -s
# more information on signatures at https://vatlab.github.io/sos-docs/doc/user_guide/signature.html

# eventually, you may also want to clean up ~/.sos/tasks/
rm -R ~/.sos/tasks/
```


## License

This is [Free Software](https://www.gnu.org/philosophy/free-sw.html) distributed under the [GNU General Public License v3.0](https://choosealicense.com/licenses/gpl-3.0/).