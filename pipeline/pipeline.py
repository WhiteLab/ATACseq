import sys
import os
import logging
import subprocess
import xml.etree.ElementTree as ET
sys.path.append('/home/ubuntu/src/ATACseq/pipeline/components')
from pipeline_software_base import PipelineSoftwareBase
from software_config_service import SoftwareConfigService
from pipeline_software import *

def main():
	import argparse
	parser = argparse.ArgumentParser(description='ATACseq pipeline')
	
# TODO How does global variable affect multithreading?
log = logging.getLogger('log')

def run_ATACseq_pipeline(software_config_path, fastq_files, fastq_dir):
    log.info('Running ATACseq pipeline')
    
    # Preprocess fastq filenames
    fastq_files_prefix = [fastq_files[0].split('.')[0], fastq_files[1].split('.')[0]]
    # If the first element in list is not the first read group, switch the elements
    if fastq_files_prefix[0].split('_')[6] != '1':
        fastq_files_prefix[0], fastq_files_prefix[1] = fastq_files_prefix[1], fastq_files_prefix[1]
    # Get the library prefix
    lib_prefix = '_'.join(fastq_files_prefix[0].split('_')[:6])
    
    # Inject SoftwareConfigService
    PipelineSoftwareBase.set_software_config_service(SoftwareConfigService(software_config_path))
    
    # Create software instances
    gzip = Gzip()
    fastx_clipper = FastxClipper()
    gunzip = Gunzip()
    fastqc = FastQC()
    bwa_aln = BwaAln()
    bwa_sampe = BwaSampe()
    samtools_view = SamtoolsView()
    fseq = FSeq()
    macs2 = MACS2()
    bedtools = Bedtools()
    picard_mark_duplicates = PicardMarkDuplicates()
    igv_tools = IGVTools()
    script_sam_stats = ScriptSamStats()
    script_recover_fragments = ScriptRecoverFragments()
    cutadapt = CutAdapt()
    
    # Pipeline step: gunzip files
#    log.info('Gunzipping files')
#    for fastq in fastq_files:
#        gunzip.generate_cmd({}, {
#            'input_file':fastq
#        }).run()
        
        
    
    # Pipeline step: fastx_clipper
    # Input files start out as .txt, but I like to change it
    # to .fastq so that it's more obvious what it is
    
    # This is the paired-end run of cutadapt
    log.info('Running pair-end cutadapt')
    cutadapt.generate_cmd({
        'output_file1': fastq_files_prefix[0] + '.clipped.fastq.gz',
        'output_file2': fastq_files_prefix[1] + '.clipped.fastq.gz'
    }, {
        'input_file1': fastq_files_prefix[0] + '.txt.gz',
        'input_file2': fastq_files_prefix[1] + '.txt.gz'
    }).run()
    
    
    # This is the single-end run of cutadapt
#    log.info('Running cutadapt')
#    for fastq in fastq_files_prefix:
#        cutadapt.generate_cmd({
#            'output_file': fastq + '.clipped.fastq'
#        }, {
#            'input_file': fastq + '.txt'
#        }).run()
        
        
    # This is the fastx_clipper run
#    for fastq in fastq_files_prefix:
#        fastx_clipper.generate_cmd({
#            'input_file':fastq + '.txt',
#            'output_file':fastq + '.clipped.fastq'
#        }, {}).run()
        
    # Pipeline step: FastQC files
    # TODO Are we interested in parsing output?
    fastqc_output_dir = fastq_dir + 'fastqc_output/'
    subprocess.call('mkdir -p ' + fastqc_output_dir, shell=True)
    
    log.info('Running FastQC')
    for fastq in fastq_files_prefix:
        fastqc.generate_cmd({
            'out_dir':fastqc_output_dir
        }, {
            'input_file':fastq + '.clipped.fastq.gz'
        }).run()
    
    # Check FastQC output
    fastqc_html_files = filter(None, 
        map(lambda x: x if '.html' in x else None, os.listdir(fastqc_output_dir)))
    if(not good_fastqc_output(fastqc_output_dir, fastqc_html_files)):
        pass
        # TODO something is wrong
    
    # Pipeline step: Gzip fastq files
#    for fastq in fastq_files_prefix:
#        gzip.generate_cmd({}, {
#            'input_file':fastq + '.clipped.fastq'
#        }).run()
    
    # Pipeline step: Align with bwa aln, then run bwa sampe
    for fastq in fastq_files_prefix:
        bwa_aln.generate_cmd({}, {
            'input_file':fastq + '.clipped.fastq.gz',
            'output_file':fastq + '.sai'
        }).run()
        
    
    bwa_sampe.generate_cmd({}, {
        'sai_1':fastq_files_prefix[0] + '.sai',
        'sai_2':fastq_files_prefix[1] + '.sai',
        'fastq_1':fastq_files_prefix[0] + '.clipped.fastq.gz',
        'fastq_2':fastq_files_prefix[1] + '.clipped.fastq.gz',
        'output_file':lib_prefix + '.sam'
    }).run()
    
    
    samtools_view.generate_cmd({
        'output_file':lib_prefix + '.12.sam'
    }, {
        'input_file':lib_prefix + '.sam'
    }).run()
    
    script_sam_stats.generate_cmd({}, {
        'input_file':lib_prefix + '.12.sam',
        'output_file':lib_prefix + '.12.sam.stats'
    }).run()
    
    script_recover_fragments.generate_cmd({}, {
        'input_file':lib_prefix + '.12.sam',
        'output_file':lib_prefix + '.frag.bed'
    }).run()
    
    # TODO Run perl script to get alignment stats
    # TODO Run perl script to recover fragments
        
    
        
        
    # TODO this is temporary
    for fastq in fastq_files_prefix:
        gzip.generate_cmd({}, {
            'input_file':fastq + '.txt'
        }).run()
    
    # Pipeline step: re-gzip files
#    for fastq in fastq_files_prefix:
#        gzip.generate_cmd({}, {
#            'input_file':fastq + '.clipped.fastq'
#        }).run()
    
    
    # Run fastx_clipper
#    Gzip().generate_cmd({}, {
#        'input_file':fastq_files[0]
#    }).run()
#    FastxClipper().generate_cmd({
#        'input_file':'input.fastq.1',
#        'output_file':'input.clipped.fastq.1'
#    }, {}).run()
#    Gunzip().generate_cmd({}, {'input_file':'input.clippsed.fastq.1'}).run()
    
    
    
    # TODO Check to make sure we're in the correct directory
    log.info('ATACseq pipeline ran successfully')
    
def good_fastqc_output(fastqc_output_dir, fastqc_html_files):
    for html in fastqc_html_files:
        tree = ET.parse(fastqc_output_dir + html)
        root = tree.getroot()
        lis = root.iter('li')
        fastqc_stats = []
        for li in lis:
            fastqc_stats.append(li[0].attrib['alt'])
        # TODO What's the threshold
    return True
