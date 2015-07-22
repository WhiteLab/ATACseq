import subprocess
import re
import logging
from software_config_service import SoftwareConfigService

log = logging.getLogger('log')

class PipelineSoftwareBase:
    ''' Superclass for a generic pipeline software'''
    software_config_service = None

    def __init__(self, software_name, software_config_service=None):
        self.software_name = software_name
        # If SoftwareConfig is given, try to inject
        # Otherwise, check to make sure ComponentConfig is injected
        # If not, raise exception
        if software_config_service:
            self.set_software_config_service(software_config_service)
        elif not PipelineSoftwareBase.software_config_service:
            raise Exception('Must inject SoftwareConfigService before instantiating')
        self.software_config = (
            PipelineSoftwareBase.software_config_service.get_software_config(self.software_name))
        self.run_cmd = ''
    
    @classmethod
    def set_software_config_service(cls, software_config_service):
        if (not cls.software_config_service 
        and isinstance(software_config_service, SoftwareConfigService)):
            cls.software_config_service = software_config_service
    
    def run(self):
        # TODO Maybe raise exception?
        if not self.run_cmd:
            log.error('Software run command has not yet been generated. '
                + 'This software will NOT run.')
        
        print '########'
        print self.run_cmd
        print '########'
        
    def generate_cmd(self, flags_args_dict, arguments_args_dict):
        path = self.get_path()
        flags = self.get_flags(flags_args_dict)
        arguments = self.get_arguments(arguments_args_dict)
        self.run_cmd = ' '.join([path, flags, arguments])
        return self
        
    def get_run_cmd(self):
        return self.run_cmd
        
    def get_path(self):
        return self.software_config['path']
        
    def get_flags(self, args_dict):
        # Get raw config lists
        flags_config = self.software_config['flags']
        singletons_config = flags_config['singletons']
        arguments_config = flags_config['arguments']
        
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
        arguments_config = self.software_config['arguments']
        arguments = ' '.join(arguments_config)
        arguments = self.replace_var_keys(arguments, args_dict)
        
        # Return constructed arguments string
        return arguments
        
    def replace_var_keys(self, var_keys_str, args_dict):
        curlies = re.findall(r'{(\S+)}', var_keys_str)
        for var_key in curlies:
            if var_key in args_dict:
                var_keys_str = var_keys_str.replace('{' + var_key + '}', args_dict[var_key])
        return var_keys_str

