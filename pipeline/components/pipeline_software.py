from pipeline_software_base import PipelineSoftwareBase

## Any software component should inherit from PipelineSoftwareBase

## For out-of-the-box behavior, just call the parent __init__() function
## and pass in self and the name of the software as it appears in the
## software_config JSON file

## To customize behavior, override:
##   get_flags(self, args_dict)
##   get_arguments(self, args_dict)
##   run(self)

class FastxClipper(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'fastx_clipper')

class Gunzip(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'gunzip')
        
class Gzip(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'gzip')
