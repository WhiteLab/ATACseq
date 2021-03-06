from pipeline_software_base import PipelineSoftwareBase

## Any software component should inherit from PipelineSoftwareBase

## For out-of-the-box behavior, just call the parent __init__() function
## and pass in self and the name of the software as it appears in the
## software_config JSON file

## To customize behavior, override:
##   get_flags(self, args_dict)
##   get_arguments(self, args_dict)
##   run(self, pipe=None)        
class Software(PipelineSoftwareBase):
    def __init__(self, name):
        PipelineSoftwareBase.__init__(self, name)
        #super(Software, self).__init__()

class FastQC(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'fastqc')
        
class BwaAln(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'bwa_aln')
        
class BwaSampe(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'bwa_sampe')
        
class SamtoolsView(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'samtools_view')
        
class SamtoolsFlagstat(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'samtools_flagstat')
        
class FSeq(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'FSeq')

class MACS2(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'MACS2')
        
class Bedtools(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'bedtools')
        
class PicardMarkDuplicates(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'picard_MarkDuplicates')
        
class IGVTools(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'IGVTools')
        
class ScriptRecoverFragments(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'script_recover_fragments')
        
class CutAdapt(PipelineSoftwareBase):
    def __init__(self):
        PipelineSoftwareBase.__init__(self, 'cutadapt_pe')
