import sys
import os
import logging
import subprocess
import xml.etree.ElementTree as ET
sys.path.append('/home/ubuntu/src/ATACseq/pipeline/components')
from pipeline_software_base import PipelineSoftwareBase, SoftwareConfigService
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
    fastqc = FastQC()
    bwa_aln = BwaAln()
    bwa_sampe = BwaSampe()
    samtools_view = SamtoolsView()
    samtools_flagstat = SamtoolsFlagstat()
    fseq = FSeq()
    macs2 = MACS2()
    picard_mark_duplicates = PicardMarkDuplicates()
    script_recover_fragments = ScriptRecoverFragments()
    cutadapt = CutAdapt()
    
    novosort = Software('novosort')
    bedtools_intersect = Software('bedtools_intersect')
    bedtools_bamtobed = Software('bedtools_bamtobed')
    igvtools_sort = Software('igvtools_sort')
    igvtools_count = Software('igvtools_count')
    script_offset_ATACseq = Software('script_offset_ATACseq')
    
    # Make temporary directory
    tmp_dir = fastq_dir + 'tmp/'
    subprocess.call('mkdir -p ' + tmp_dir, shell=True)
        
    ###########################
    # Pipeline step: cutadapt
    # Input files start out as .txt, but I like to change it
    # to .fastq so that it's more obvious what it is
    
    # This is the paired-end run of cutadapt
    log.info('Running pair-end cutadapt')
    cutadapt.generate_cmd({
        'output_file1': fastq_files_prefix[0] + '.clipped.fastq.gz',
        'output_file2': fastq_files_prefix[1] + '.clipped.fastq.gz',
        'min_quality_score': '30',
        'quality_base': '64',
        'input_file1': fastq_files_prefix[0] + '.txt.gz',
        'input_file2': fastq_files_prefix[1] + '.txt.gz'
    }).run()
    
    # Make directory for FastQC output
    fastqc_output_dir = fastq_dir + 'fastqc_output/'
    subprocess.call('mkdir -p ' + fastqc_output_dir, shell=True)
    
    log.info('Running FastQC')
    # Run the steps in this for loop separately for each fastq file
    for fastq in fastq_files_prefix:
        #########################
        # Pipeline step: FastQC 
        # Get QC stats for fastq files
        # TODO Are we interested in parsing output?
        fastqc.generate_cmd({
            'out_dir': fastqc_output_dir,
            'input_file': fastq + '.clipped.fastq.gz'
        }).run()
        
        ##########################
        # Pipeline step: bwa aln
        # Generate suffix array for bwa aligner
        # Done for each fastq file
        bwa_aln.generate_cmd({
            'input_file':fastq + '.clipped.fastq.gz',
            'output_file':fastq + '.sai'
        }).run()
        
    ############################
    # Pipeline step: bwa sampe
    # Align reads in fastq files to reference
    # Output in sorted BAM format
    bwa_sampe.generate_cmd({
        'sai_1':fastq_files_prefix[0] + '.sai',
        'sai_2':fastq_files_prefix[1] + '.sai',
        'fastq_1':fastq_files_prefix[0] + '.clipped.fastq.gz',
        'fastq_2':fastq_files_prefix[1] + '.clipped.fastq.gz'
    }, pipe=(
        samtools_view.generate_cmd({
            'singletons': '-hSb',
            'input_file': '-',
            'output_file': lib_prefix + '.bam'
        })
    )).run()
    
    novosort.generate_cmd({
        'tmpdir': tmp_dir,
        'input_file': lib_prefix + '.bam',
        'output_file': lib_prefix + '.sorted.bam'
    }).run()
    
    ################################
    # Pipeline step: samtools flagstat
    # Generate alignment statistics
    
    samtools_flagstat.generate_cmd({
        'input_file': lib_prefix + '.bam',
        'output_file': lib_prefix + '.bam.flagstat'
    }).run()
    
    ####################################
    # Pipeline step: recover fragments
    # Whatever that actually means
    
    #####################################################
    # Pipeline step: Generate genome coverage bed files
    
    #####################################################
    # Pipeline step: Remove blacklisted genomic regions
    bedtools_intersect.generate_cmd({
        'input_file': lib_prefix + '.sorted.bam',
        'blacklist_bed': '/mnt/cinder/dfitzgeraldSCRATCH/annotation/hg19_blacklisted/hg19-blacklist.bed',
        'output_file': lib_prefix + '.bl.sorted.bam'
    }).run()
    
    bedtools_bamtobed.generate_cmd({
        'input_file': lib_prefix + '.bl.sorted.bam',
        'output_file': lib_prefix + '.bl.sorted.bed'
    }).run()
    
    ### TODO Do we need to remove unaligned reads before peak calling?
    ### Even if we want to keep them in BAMs, should they be removed later?
    
    ###################################################
    # Pipeline step: Generate .tdf file with IGVTools
    igvtools_sort.generate_cmd({
        'tmp_dir': tmp_dir,
        'input_file': lib_prefix + '.bl.sorted.bed',
        'output_file': lib_prefix + '.bl.igvsorted.bed'
    }).run()
    
    igvtools_count.generate_cmd({
        'input_file': lib_prefix + '.bl.igvsorted.bed',
        'output_file': lib_prefix + '.tdf',
        'genome_sizes_file': '/mnt/cinder/dfitzgeraldSCRATCH/annotation/hg19_chrom_sizes/hg19.chrom.sizes'
    }).run()
    
    ## Start processing files for peak calling
    for partial_bed in ['99', '147', '83', '163']:
        samtools_view.clear_flags().add_flag_with_argument('-bf', [partial_bed]).generate_cmd({
            'input_file': lib_prefix + '.sorted.bam'
        }, pipe=(
            bedtools_bamtobed.generate_cmd({
                'input_file': 'stdin',
                'output_file': lib_prefix + '.' + partial_bed + '.bl.sorted.bed'
            })
        )).run()
    
    script_offset_ATACseq.generate_cmd({
        'input_beds_prefix': lib_prefix
    }).run()
    
    
    # Pipeline step: Peak calling
    
    
    
    
    
    
#    script_recover_fragments.generate_cmd({
#        'input_file':lib_prefix + '.12.sam',
#        'output_file':lib_prefix + '.frag.bed'
#    }).run()
    
    # TODO Run perl script to get alignment stats
    # TODO Run perl script to recover fragments
    
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

