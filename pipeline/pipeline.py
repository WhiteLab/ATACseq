import sys
import logging
sys.path.append('/home/ubuntu/src/ATACseq/pipeline/components')
from pipeline_software_base import PipelineSoftwareBase
from software_config_service import SoftwareConfigService
from pipeline_software import *

def main():
	import argparse
	parser = argparse.ArgumentParser(description='ATACseq pipeline')
	
# TODO How does global variable affect multithreading?
log = logging.getLogger('log')

def run_ATACseq_pipeline(software_config_path, fastq_files, ref_mnt):
    log.info('Running ATACseq pipeline')
    
    # Inject SoftwareConfigService
    PipelineSoftwareBase.set_software_config_service(SoftwareConfigService(software_config_path))
    
    # Run fastx_clipper
    Gzip().generate_cmd({}, {
        'input_file':fastq_files[0]
    }).run()
    FastxClipper().generate_cmd({
        'input_file':'input.fastq.1',
        'output_file':'input.clipped.fastq.1'
    }, {}).run()
    Gunzip().generate_cmd({}, {'input_file':'input.clippsed.fastq.1'}).run()
    
    
    
    # TODO Check to make sure we're in the correct directory
    log.info('ATACseq pipeline ran successfully')
