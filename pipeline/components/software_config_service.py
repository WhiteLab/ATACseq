import json

class SoftwareConfigService:
    def __init__(self, config_file):
        self.software_config = json.loads(open(config_file, 'r').read())
    
    def get_software_config(self, software):
        return self.software_config[software]

