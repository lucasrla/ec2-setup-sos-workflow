# inspired by https://github.com/dcbark01/AnacondaInstallEC2/blob/master/install.sh

if ! command -v conda &> /dev/null
then
    echo "conda could not be found, will download and install miniconda"

    # cd /home/ec2-user
    # su ec2-user

    # Miniconda installer archive https://repo.anaconda.com/miniconda/
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda3.sh

    # Run the installer (installing without -p should automatically install into '/' (root dir)
    bash /tmp/miniconda3.sh -b -p /home/ec2-user/miniconda3
    rm /tmp/miniconda3.sh

    # Run the conda init script to setup the shell
    . /home/ec2-user/miniconda3/etc/profile.d/conda.sh
    source /home/ec2-user/.bashrc
    conda init
fi

# Install SoS on base environment
conda install -y -c conda-forge sos