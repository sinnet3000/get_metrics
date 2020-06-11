#!/usr/bin/python
import yaml
import re
from pssh.clients import ParallelSSHClient
import statsd
import logging
import sys
import time

class Main:
    """Main class to initialize script. """
    
    def __init__(self):
        """Read YAML configuration file and start the two main classes"""
        file = open('config.yml', 'r')
        cfg = yaml.load(file, Loader=yaml.FullLoader)
        data_sender = DataSender.factory(cfg['data_sender'])
        self.poller = Poller.factory(cfg['hosts'], data_sender)
        logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s', handlers=[
        logging.FileHandler("metrics.log"),
        logging.StreamHandler(sys.stdout) ])
        
class Poller:
    """Factory method to initialize the Poller type that is going to be used"""
    
    def factory(hosts, data_sender, poller_type='ssh'):
        if poller_type == "ssh": return SSHPoller(hosts, data_sender)
        assert 0, "Bad type: " + config["type"]
    factory = staticmethod(factory)


class SSHPoller(Poller):
    """SSH Poller, this class utilizes Parallel-SSH, so it only needs a lists of hosts and it will use the SSH configuration from the current running user"""

    def __init__(self, hosts, data_sender):
        """Overrides InformalParserInterface.load_data_source()"""
        self._hosts = hosts
        self._client = ParallelSSHClient(hosts)
        self._data_sender = data_sender
        self._host_fqdn = {}
        self.get_hostnames()
        
    def parse_memory(self, line):
        """Helper to get the amount of memory from the PS command line"""
        r = re.compile("\d+")
        return r.search(line).group()

    def get_metrics(self):
        """This method leverages parallel-ssh to connect to all our hosts of interest and grab the memory - process data using ps"""
        output = self._client.run_command('ps -o size,command ax')
        for (host, host_output) in output.items():
            for processes_per_host in host_output.stdout:
                process_list = processes_per_host.splitlines()
                for process_line in process_list:
                    for monitored_process in self._hosts[host]:
                        if monitored_process in process_line:
                            self._data_sender.send_data(self._host_fqdn[host], monitored_process, self.parse_memory(process_line))
                            
    def get_hostnames(self):
    	"""I can't use a FQDN as part of the statsd metrics name, so let's grab the hostnames"""
    	output = self._client.run_command('hostname')
    	for (host, host_output) in output.items():
    		for hostname in host_output.stdout:
    			self._host_fqdn[host] = hostname


class DataSender:
    """Factory method to initialize the DataSender type that is going to be used"""
    def factory(config):
        if config["type"] == "statsd": return StatsD(config)
        assert 0, "Bad type: " + config["type"]
    factory = staticmethod(factory)
        
class StatsD(DataSender):
    """Class that works as a wrapper for the Python StatsD library"""
    def __init__(self, config):
        self.config = config
        self.client = statsd.TCPStatsClient(config["host"], config["port"])
        
    def send_data(self, host, process_name, process_memory):
        self.client.gauge("servers.{0}.memory.{1}".format(host, process_name), int(process_memory))
        logging.info("servers.{0}.memory.{1}".format(host, process_name, process_memory))
   
if __name__ == '__main__':
    main = Main()
    while 1:
        main.poller.get_metrics()
        time.sleep(10)
