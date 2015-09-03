import sys
import subprocess
import re
import logging
import json
from copy import deepcopy
#from synapseclient import Activity, File

# This project is called Surf

log = logging.getLogger('log')

class SoftwareConfigService(object):
    def __init__(self, config_file):
        self.software_config = json.loads(open(config_file, 'r').read())
    
    def get_software_config(self, software):
        return deepcopy(self.software_config[software])

class PipelineSoftwareBase(object):
    '''
    Superclass for a generic pipeline software
    '''
    software_config_service = None


    def __init__(self, software_name, software_config_service_inject=None):
        self.software_name = software_name
        # Try to inject SoftwareConfigService
        self.set_software_config_service(software_config_service_inject)
        
        # Check to make sure SoftwareConfigService is present
        # If not, raise exception
        if not PipelineSoftwareBase.software_config_service:
            raise Exception('Must inject SoftwareConfigService before instantiating')
        self.software_config = {}
        self.get_default_software_config()
        self.run_cmd = None
        self.piped_cmd = None
        
        # Set logging
        format_str = '%(asctime)s> %(message)s'
        datefmt_str = '%Y%b%d %H:%M:%S'
        self.log = logging.getLogger(self.software_name)
        log_file_path = self.software_name + '.run.log' # TODO this might change
        self.handler = logging.FileHandler(log_file_path)
        self.handler.setFormatter(logging.Formatter(fmt=format_str, datefmt=datefmt_str))
        self.log.addHandler(self.handler)
        self.log.debug('Attached log file for ' + self.software_name)
    
    
    @classmethod
    def set_software_config_service(cls, software_config_service):
        if (not cls.software_config_service 
        and isinstance(software_config_service, SoftwareConfigService)):
            cls.software_config_service = software_config_service
    
    
    def get_default_software_config(self):
        self.software_config = (
            PipelineSoftwareBase.software_config_service.get_software_config(self.software_name))
        if 'flags' not in self.software_config:
            self.software_config['flags'] = {}
        else:
            if 'singletons' not in self.software_config['flags']:
                self.software_config['flags']['singletons'] = []
            if 'arguments' not in self.software_config['flags']:
                self.software_config['flags']['arguments'] = {}
        if 'arguments' not in self.software_config:
            self.software_config['arguments'] = []
    
    
    def restore_default_config(self):
        self.get_default_software_config()
        return self
    
    
    def add_flag(self, flag):
        self.software_config['flags']['singletons'].append(flag)
        return self
    
    
    def add_flag_with_argument(self, flag, argument):
        if not isinstance(argument, list):
            argument = [argument]
        self.software_config['flags']['arguments'][flag] = argument
        return self
        
    
    def remove_flag(self, flag):
        if flag in self.software_config['flags']['singletons']:
            self.software_config['flags']['singletons'].remove(flag)
        elif flag in self.software_config['flags']['arguments']:
            del self.software_config['flags']['arguments'][flag]
        return self
    
    
    def clear_flags(self):
        self.software_config['flags']['singletons'] = []
        self.software_config['flags']['arguments'] = {}
        return self
    
    
    def append_argument(self, argument):
        self.software_config['arguments'].append(argument)
        return self
        
    
    def pop_argument(self):
        self.software_config['arguments'].pop()
        return self
    
    
    def clear_arguments(self):
        self.software_config['arguments'] = []
        return self
        
    
    def run(self):
        # TODO Maybe raise exception?
        if not self.run_cmd:
            log.error('Software run command has not yet been generated. '
                + 'This software will NOT run.')
        
        # If a pipe command was given, add it to this command
        if self.piped_cmd != None:
            popen_run_cmd = self.run_cmd + ' | ' + self.piped_cmd
        else:
            popen_run_cmd = self.run_cmd
        
        # Log command into logs
        log.debug('Running command: ' + popen_run_cmd)
        self.log.debug('Running command: ' + popen_run_cmd)
        
        # Run commands, logging output
        s = subprocess.Popen(popen_run_cmd, shell=True, stdout=subprocess.PIPE, stderr=sys.stdout.fileno())
        while True:
            line = s.stdout.readline().rstrip('\n')
            if not line:
                break
            self.log.info(line)
        
        # Piped command should not be persistent
        self.piped_cmd = None
        return self
    
        
    def generate_cmd(self, cmd_vars={}, pipe=None):
        path = self.get_path()
        flags = self.get_flags(cmd_vars)
        arguments = self.get_arguments(cmd_vars)
        stdout = self.get_stdout(cmd_vars)
        stderr = self.get_stderr(cmd_vars)
        self.run_cmd = ' '.join([path, flags, arguments, stdout, stderr])
        
        # If a pipe command was given, store it for later execution
        if isinstance(pipe, PipelineSoftwareBase):
            self.piped_cmd = pipe.get_run_cmd()
        elif type(pipe) == str:
            self.piped_cmd = pipe
        
        # Return self for chaining
        return self
    
        
    def get_run_cmd(self):
        return self.run_cmd
    
        
    def get_path(self):
        return self.software_config['path'] if 'path' in self.software_config else ''
    
        
    def get_flags(self, args_dict):
        # Get raw config lists
        flags_config = self.software_config['flags'] if 'flags' in self.software_config else {}
        singletons_config = flags_config['singletons'] if 'singletons' in flags_config else []
        arguments_config = flags_config['arguments'] if 'arguments' in flags_config else {}
        
        # Parse singletons, easy
        singletons = ' '.join(singletons_config)
        
        # Parse flags with arguments
        arguments = []
        for flag in arguments_config:
            flag_elements = [flag]
            for arg in arguments_config[flag]:
                flag_elements.append(arg)
            arguments.append(' '.join(flag_elements))
        arguments = ' '.join(arguments)
        
        # Join singletons and flags with arguments
        full_flags = ' '.join([singletons, arguments])
        
        # Replace any {variable_keys}
        full_flags = self.replace_var_keys(full_flags, args_dict)
        
        # Return constructed flags string
        return full_flags
    
    
    def get_arguments(self, args_dict):
        # Parse arguments list, replace {variable_keys}
        arguments_config = self.software_config['arguments'] if 'arguments' in self.software_config else []
        arguments = ' '.join(arguments_config)
        arguments = self.replace_var_keys(arguments, args_dict)
        
        # Return constructed arguments string
        return arguments
        
        
    def get_stdout(self, cmd_vars):
        stdout = self.software_config['stdout'] if 'stdout' in self.software_config else ''
        if stdout != '':
            return '1> ' + self.replace_var_keys(stdout, cmd_vars)
        return ''
    
            
    def get_stderr(self, cmd_vars):
        stderr = self.software_config['stderr'] if 'stderr' in self.software_config else ''
        if stderr != '':
            return '2> ' + self.replace_var_keys(stderr, cmd_vars)
        return ''
    
        
    def replace_var_keys(self, var_keys_str, args_dict):
        curlies = re.findall(r'{(\S+)}', var_keys_str)
        for var_key in curlies:
            if var_key in args_dict:
                var_keys_str = var_keys_str.replace('{' + var_key + '}', args_dict[var_key])
        return var_keys_str
    
        
    def print_help(self):
        # TODO I want this to print out usage for this software
        print 'Help for ' + self.software_name
    
    def add_provenance(self):
        prov_config = self.software_config['synapse']
        syn_inputs = []

    def remove_log_handler(self):
        self.log.removeHandler(self.handler)
        
    def __del__(self):
        self.log.removeHandler(self.handler)
