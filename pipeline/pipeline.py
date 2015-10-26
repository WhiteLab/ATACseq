import sys
import os
import logging
import subprocess
import xml.etree.ElementTree as ET
sys.path.append('/home/ubuntu/pipelines/ATACseq/pipeline/components')
from pipeline_software_base import PipelineSoftwareBase, SoftwareConfigService
from pipeline_software import *


def main():
	import argparse
	parser = argparse.ArgumentParser(description='ATACseq pipeline')
	
# TODO How does global variable affect multithreading?
log = logging.getLogger('log')

def run_ATACseq_pipeline(software_config_path, fastq_files, fastq_dir, parent_syn_id, step=0):
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
    script_recover_fragments = ScriptRecoverFragments()
    cutadapt = CutAdapt()
    
    novosort = Software('novosort')
    bedtools_intersect = Software('bedtools_intersect')
    bedtools_bamtobed = Software('bedtools_bamtobed')
    bedtools_merge = Software('bedtools_merge')
    igvtools_sort = Software('igvtools_sort')
    igvtools_count = Software('igvtools_count')
    script_offset_ATACseq = Software('script_offset_ATACseq')
    macs2_callpeak = Software('MACS2_callpeak')
    picard_mark_duplicates = Software('picard_MarkDuplicates')
    homer_findpeaks = Software('HOMER_findPeaks')
    homer_maketagdirectory = Software('HOMER_makeTagDirectory')
    homer_pos2bed = Software('HOMER_pos2bed')
    sicer_rb = Software('SICER_rb')
    
    # Make temporary directory
    tmp_dir = fastq_dir + 'tmp/'
    subprocess.call('mkdir -p ' + tmp_dir, shell=True)
    
#    syn_file_raw_fastqs = []
#    for i, fastq in enumerate(fastq_files_prefix):
#        syn_fastq = File(
#            path='',
#            name='Raw ATACseq fastq ' + str(i),
#            parent=parent_syn_id
#        )
        
    # Pipeline Step 1
    if step <= 1:
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
            'quality_base': '33',
            'input_file1': fastq_files_prefix[0] + '.txt.gz',
            'input_file2': fastq_files_prefix[1] + '.txt.gz',
            'summary_file': lib_prefix + '.cutadapt.summary.log'
        }).run()
    
#    syn_act_cutadapt = Activity(
#        name='Cutadapt Paired-end',
#        description='Cutadapt Paired-end, trimming to adapters and quality >= 30',
#        used=[syn_file_raw_fastqs[0], syn_file_raw_fastq[1]],
#        executed=cutadapt.get_path()
#    )
#    
#    syn_file_clipped_fastqs = []
    
    # Pipeline Step 2
    if step <= 2:
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
                'input_file': fastq + '.clipped.fastq.gz',
                'output_file': fastq + '.sai',
                'output_log': 'bwa_aln.summary.log'
            }).run()
      
    # Pipeline Step 3
    if step <= 3:  
        ############################
        # Pipeline step: bwa sampe
        # Align reads in fastq files to reference
        # Output in sorted BAM format
        bwa_sampe.generate_cmd({
            'sai_1': fastq_files_prefix[0] + '.sai',
            'sai_2': fastq_files_prefix[1] + '.sai',
            'fastq_1': fastq_files_prefix[0] + '.clipped.fastq.gz',
            'fastq_2': fastq_files_prefix[1] + '.clipped.fastq.gz',
            'output_log': 'bwa_sampe.summary.log'
        }, pipe=(
            samtools_view.generate_cmd({
                'input_file': '-',
                'output_file': lib_prefix + '.bam'
            })
        )).run()
    
    
    # If this actually works, it will only output unique reads
#    bwa_sampe.generate_cmd({
#        'sai_1':fastq_files_prefix[0] + '.sai',
#        'sai_2':fastq_files_prefix[1] + '.sai',
#        'fastq_1':fastq_files_prefix[0] + '.clipped.fastq.gz',
#        'fastq_2':fastq_files_prefix[1] + '.clipped.fastq.gz'
#    }, pipe=(
#        grep_unique_alignments.generate_cmd({}, pipe=(
#            samtools_view.generate_cmd({
#                'input_file': '-',
#                'output_file': lib_prefix + '.bam'
#            })
#        ))
#    )).run()
    
    ################################
    # Pipeline step: samtools flagstat
    # Generate alignment statistics
    
    # Pipeline Step 4
    if step <= 4:
        samtools_flagstat.generate_cmd({
            'input_file': lib_prefix + '.bam',
            'output_file': lib_prefix + '.bam.flagstat'
        }).run()
        
        # Proceed with only uniquely mapped reads
        (samtools_view.clear_flags().add_flag('-b')
            .add_flag_with_argument('-F', ['256'])
            .add_flag_with_argument('-q', ['10'])
            .add_flag_with_argument('-o', [lib_prefix + '.unique.bam'])
            .generate_cmd({
                'input_file': lib_prefix + '.bam'
            }).run()
        )
    
        novosort.generate_cmd({
            'tmp_dir': tmp_dir,
            'input_file': lib_prefix + '.unique.bam',
            'output_file': lib_prefix + '.sorted.unique.bam',
            'output_log': 'novosort.summary.log'
        }).run()
        
        picard_mark_duplicates.generate_cmd({
            'input_file': lib_prefix + '.sorted.unique.bam',
            'output_file': lib_prefix + '.duprm.sorted.unique.bam',
            'metrics_file': lib_prefix + '.markduplicates.metrics.log',
            'tmp_dir': tmp_dir,
            'output_log': 'Picard_MarkDuplicates.summary.log'
        }).run()
        
        (samtools_view.clear_flags().add_flag('-b')
            .add_flag_with_argument('-F', ['12'])
            .add_flag_with_argument('-o', [lib_prefix + '.unmappedrm.duprm.sorted.unique.bam'])
            .generate_cmd({
                'input_file': lib_prefix + '.duprm.sorted.unique.bam'
            }).run()
        )
    
    # Pipeline Step 5
    if step <= 5:
        #####################################################
        # Pipeline step: Remove blacklisted genomic regions
        bedtools_intersect.generate_cmd({
            'input_file': lib_prefix + '.unmappedrm.duprm.sorted.unique.bam',
            'blacklist_bed': '/mnt/cinder/dfitzgeraldSCRATCH/annotation/hg19_blacklisted/hg19-blacklist.bed',
            'output_file': lib_prefix + '.bl.unmappedrm.duprm.sorted.unique.bam'
        }).run()
    
#    bedtools_bamtobed.generate_cmd({
#        'input_file': lib_prefix + '.bl.unmappedrm.duprm.sorted.unique.bam',
#        'output_file': lib_prefix + '.bl.unmappedrm.duprm.sorted.unique.bed'
#    }).run()
    
    # Pipeline Step 6
    if step <= 6:
        # Separate into single-end strands for peak calling, +/- strand for .tdf generation
        for sam_flag in [['64', 'readgroup1'], ['128', 'readgroup2'], ['16', 'minusstrand'], ['32', 'plusstrand']]:
            samtools_view.clear_flags().add_flag_with_argument('-bf', [sam_flag[0]]).generate_cmd({
                'input_file': lib_prefix + '.bl.unmappedrm.duprm.sorted.unique.bam'
            }, pipe=(
                bedtools_bamtobed.generate_cmd({
                    'input_file': 'stdin',
                    'output_file': lib_prefix + '.' + sam_flag[1] + '.bl.unmappedrm.duprm.sorted.unique.bed'
                })
            )).run()
    
    # Pipeline Step 7
    if step <= 7:
        # Shift bed files for .tdf generation
        for directionality in ['minusstrand', 'plusstrand']:
            with open(lib_prefix + '.' + directionality + '.bl.unmappedrm.duprm.sorted.unique.bed') as in_bed:
                with open(lib_prefix + '.shifted.' + directionality + '.bl.unmappedrm.duprm.sorted.unique.bed', 'w') as out_bed:
                    for line in in_bed:
                        minus_strand = True if directionality == 'minusstrand' else False
                        out_bed.write(get_offset_line(line.rstrip('\n').split('\t'), minus_strand))
            
            # Generate .tdf for each +/- strand individually
            igvtools_sort.generate_cmd({
                'tmp_dir': tmp_dir,
                'input_file': lib_prefix + '.shifted.' + directionality + '.bl.unmappedrm.duprm.sorted.unique.bed',
                'output_file': lib_prefix + '.shifted.' + directionality + '.bl.unmappedrm.duprm.igvsorted.unique.bed'
            }).run()
            
            igvtools_count.generate_cmd({
                'input_file': lib_prefix + '.shifted.' + directionality + '.bl.unmappedrm.duprm.igvsorted.unique.bed',
                'output_file': lib_prefix + '.' + directionality + '.tdf',
                'genome_sizes_file': '/mnt/cinder/dfitzgeraldSCRATCH/annotation/hg19_chrom_sizes/hg19.chrom.sizes'
            }).run()
        
        # Combine +/- bed files, generate .tdf from that
        combine_beds = ('cat ' + lib_prefix + '.shifted.minusstrand.bl.unmappedrm.duprm.sorted.unique.bed '
            + lib_prefix + '.shifted.plusstrand.bl.unmappedrm.duprm.sorted.unique.bed >'
            + lib_prefix + '.combined.shifted.bl.unmappedrm.duprm.sorted.unique.bed')
        subprocess.call(combine_beds, shell=True)
        
        bedtools_merge.generate_cmd({
            'input_file': lib_prefix + '.combined.shifted.bl.unmappedrm.duprm.sorted.unique.bed',
            'output_file': lib_prefix + '.merged.shifted.bl.unmappedrm.duprm.sorted.unique.bed'
        }).run()
        
        igvtools_sort.generate_cmd({
            'tmp_dir': tmp_dir,
            'input_file': lib_prefix + '.merged.shifted.bl.unmappedrm.duprm.sorted.unique.bed',
            'output_file': lib_prefix + '.merged.shifted.bl.unmappedrm.duprm.igvsorted.unique.bed'
        }).run()
        
        igvtools_count.generate_cmd({
            'input_file': lib_prefix + '.merged.shifted.bl.unmappedrm.duprm.igvsorted.unique.bed',
            'output_file': lib_prefix + '.merged.tdf',
            'genome_sizes_file': '/mnt/cinder/dfitzgeraldSCRATCH/annotation/hg19_chrom_sizes/hg19.chrom.sizes'
        }).run()
    
    # Pipeline Step 8
    if step <= 8:
        # Peak Calling
        #for read in ["read1", "read2"]:
        for read in ['singleend']:		
            #MACS2 Peak Calling
            macs2_output_dir = fastq_dir + 'macs2_' + read + '_output/'
            subprocess.call('mkdir -p ' + macs2_output_dir, shell=True)
            
            macs2_callpeak.generate_cmd({
                'output_dir': macs2_output_dir,
                'input_bed': lib_prefix + '.' + read + '.bl.unmappedrm.duprm.sorted.unique.bed',
                'lib_prefix': lib_prefix,
                'output_log': 'MACS2_callpeak.' + read + '.summary.log'
            }).run()
            
            # HOMER Peak Calling
            homer_tagdir = fastq_dir + 'HOMER_tagdir_' + read + '/'
            
            homer_maketagdirectory.generate_cmd({
                'input_bed': lib_prefix + '.' + read + '.bl.unmappedrm.duprm.sorted.unique.bed',
                'out_tag_directory': homer_tagdir,
                'output_log': 'HOMER_maketagdir.' + read + '.summary.log'
            }).run()
            
            homer_findpeaks.generate_cmd({
                'tag_directory': homer_tagdir,
                'output_log': 'HOMER_findpeaks.' + read + '.summary.log'
            }).run()
            
            homer_pos2bed.generate_cmd({
                'input_txt': homer_tagdir + 'regions.txt',
                'output_bed': homer_tagdir + lib_prefix + '.regions.bed',
                'output_log': 'HOMER_pos2bed.' + read + '.summary.log'
            }).run()
            
            # SICER Peak Calling
#            sicer_output_dir = fastq_dir + 'SICER_' + read + '_output/'
#            subprocess.call('mkdir -p ' + sicer_output_dir, shell=True)
#            sicer_rb.generate_cmd({
#                'input_dir': fastq_dir,
#                'input_bed': lib_prefix + '.' + read + '.bl.unmappedrm.duprm.sorted.unique.bed',
#                'output_dir': sicer_output_dir,
#                'output_log': 'SICER.' + read + '.summary.log'
#            }).run()
    
    
    ###################################################
    # Pipeline step: Generate .tdf file with IGVTools
#    igvtools_sort.generate_cmd({
#        'tmp_dir': tmp_dir,
#        'input_file': lib_prefix + '.bl.unmappedrm.duprm.sorted.unique.bed',
#        'output_file': lib_prefix + '.bl.unmappedrm.duprm.igvsorted.unique.bed'
#    }).run()
#    
#    igvtools_count.generate_cmd({
#        'input_file': lib_prefix + '.bl.unmappedrm.duprm.igvsorted.unique.bed',
#        'output_file': lib_prefix + '.tdf',
#        'genome_sizes_file': '/mnt/cinder/dfitzgeraldSCRATCH/annotation/hg19_chrom_sizes/hg19.chrom.sizes'
#    }).run()
#    
#    ## Start processing files for peak calling
#    for partial_bed in ['99', '147', '83', '163']:
#        samtools_view.clear_flags().add_flag_with_argument('-bf', [partial_bed]).generate_cmd({
#            'input_file': lib_prefix + '.bl.unmappedrm.duprm.sorted.unique.bam'
#        }, pipe=(
#            bedtools_bamtobed.generate_cmd({
#                'input_file': 'stdin',
#                'output_file': lib_prefix + '.' + partial_bed + '.bl.unmappedrm.duprm.sorted.unique.bed'
#            })
#        )).run()
#    
#    script_offset_ATACseq.generate_cmd({
#        'input_beds_prefix': lib_prefix
#    }).run()
    
    ###### Peak Calling #########
#    fseq_output_dir = fastq_dir + 'fseq_output/'
#    subprocess.call('mkdir -p ' + fseq_output_dir, shell=True)
#    macs2_output_dir = fastq_dir + 'macs2_output/'
#    subprocess.call('mkdir -p ' + macs2_output_dir, shell=True)
    
    # Pipeline step: Peak calling with Fseq
    
    # Pipeline step: Peak calling with MACS2
#    macs2_callpeak.generate_cmd({
#        'output_dir': macs2_output_dir,
#        'input_bed': lib_prefix + '.adjusted.bl.unmappedrm.duprm.sorted.unique.bed',
#        'lib_prefix': lib_prefix
#    }).run()
    
    # Clean up a bit
#    files_to_remove = (['*.clipped.fastq.gz', '*.txt.gz', '*.sai',
#        lib_prefix + '.83.bl.unmappedrm.sorted.bed', lib_prefix + '.99.bl.unmappedrm.sorted.bed',
#        lib_prefix + '.147.bl.unmappedrm.sorted.bed', lib_prefix + '.163.bl.unmappedrm.sorted.bed'])
#    for file_to_rm in files_to_remove:
#        subprocess.call('rm -rf ' + fastq_dir + file_to_rm, shell=True)
    
    
    
    
    
    
    
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


def get_offset_line(cols, is_negative_strand):
    if is_negative_strand:
        start = int(cols[1]) - 5
        stop = start + 1
    else:
        start = int(cols[1]) + 4
        stop = start + 1
    out_line = ('\t'.join([str(cols[0]), str(start), str(stop),
            str(cols[3]), str(cols[4]), str(cols[5])]) + '\n')
    return out_line
