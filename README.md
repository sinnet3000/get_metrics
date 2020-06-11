# get_metrics.py

This project is a POC for a Python based script daemon for gathering statistics metrics in Linux without using a stats daemon such as collectD. It is non-production ready and it was made for education purposes and learn more about the ParallelSSHClient and statsd Python library.

The script can gather memory usage from a process using SSH, it can connect to multiple servers via SSH and send the data to a statsd server.

The script does not need any parameters to run, the idea is that it would run as a background process, maybe a cronjob or a systemD service (needs more code to do that though) and all the config is controlled through a YAML config file which needs the address of the servers to monitor and the process names to monitor. An example YAML file is included in the project.

## Getting started

The script was tested on an Ubuntu environment, so I'd suggest is run on Linux.

You can use PIP to install all the requirements, piping the requirements.txt included in the repo

```
pip3 install -r requirements.txt
```

## Usage

You will need to edit the config.yml file to point to a Linux host (or a few) that have SSHD running, and include the process names of the files to monitor.

Then, you can execute the script with:

```
python3 get_metrics.py &
```

