import sys
import os
import subprocess
import traceback
import logging
import argparse
import json
sys.path.append('/home/ubuntu/src/ATACseq/utility')
from download_from_swift import download_from_swift
sys.path.append('/home/ubuntu/src/ATACseq/pipeline')
from pipeline import run_ATACseq_pipeline

def parse_config(config_file):
    config_data = json.loads(open(config_file, 'r').read())
    return (config_data['refs']['container'],
        config_data['refs']['obj'],
        config_data['refs']['pipeline_config'])

def main():
    parser = argparse.ArgumentParser(description='Handles running pipeline.')
    # TODO come up with more meaningful flags
    parser.add_argument('-f', '--file', help='File with Bionimbus ID, seqtype, and '
        + 'sample lane list.')
    parser.add_argument('-j', '--json', help='JSON config file with tools, references, '
        + 'data storage locations.')
    parser.add_argument('-m', '--mount', help='Reference mount drive location.')
    parser.add_argument('-v', '--verbose', action='count',
        help='Verbosity in log file. -v is INFO, -vv is DEBUG, omitted is WARNING.')
            
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    inputs = parser.parse_args()
    bid_file_path = inputs.file
    config_file = inputs.json
    ref_mnt = inputs.mount.rstrip('/')
    verbosity = inputs.verbose
    
    # Get swift data from config file
    # TODO This could probably be a bit more robust, think about more
    #container, obj, pipeline_config = parse_config(config_file)
    container, obj, pipeline_config = 'PsychENCODE', '', ''
    
    # Setup logging
    format_string = '[%(levelname)s] %(asctime)s> %(message)s'
    datefmt_string = '%Y%b%d %H:%M:%S'
    if verbosity == 1:
        log_level = logging.INFO
    elif verbosity > 1:
        log_level = logging.DEBUG
    else:
        log_level = logging.WARNING
    logging.basicConfig(format=format_string, datefmt=datefmt_string, level=log_level)
    log = logging.getLogger('log')
    log_formatter = logging.Formatter(fmt=format_string, datefmt=datefmt_string)
    
    # Source command
    src_cmd = '. /home/ubuntu/.novarc; '
    
    # Setup working directory
    cwd = ref_mnt + '/SCRATCH'
    log.info('Loading working directory ' + cwd)
    if not os.path.isdir(cwd):
        log.info('Working directory doesn\'t exist, attempting to create now')
        try:
            subprocess.check_call('mkdir -p ' + cwd, shell=True)
        except Exception as e:
            log.critical('Creating working directory ' + cwd
                + ' failed. Ensure the correct machine is being used for '
                + 'this sample set')
            log.debug('Exception: ' + str(e))
            log.debug(traceback.format_exc().rstrip('\n'))
            log.critical('Terminating run now')
            sys.exit(1)
    
    # Open bid file, read line by line
    log.info('Opening file ' + bid_file_path)
    with open(bid_file_path, 'r') as bid_file:
        for line in bid_file:
            line = line.rstrip('\n')
            # Get run info from bid file
            log.debug('Reading in line from bid file')
            bid, seqtype, lane_csv = line.split('\t') # TODO seqtype is never used
            log.debug('bid: ' + bid + ', seqtype: ' + seqtype
                + ' lane_csv: ' + lane_csv)
            
            # Change to working directory
            os.chdir(cwd)
            log.info('Changed to working directory')
            
            # Attach log file handler
            log_file_path = cwd + '/' + bid + '.run.log'
            log_file = logging.FileHandler(log_file_path)
            log_file.setFormatter(log_formatter)
            log.addHandler(log_file)
            log.info('Attached local log file at ' + log_file_path)
            
            obj_prefix = 'RAW/' + bid + '/' + bid + '_'
            fastq_dir = cwd + '/RAW/' + bid + '/'
            lane_status = {} # TODO I'm not sure what purpose this serves
            for lane in lane_csv.split(', '):
                lane_status[lane] = 'Initializing'
                log.info('Listing fastq files from swift for ' + bid)
                swift_list_cmd = (src_cmd + 'swift list ' + container
                    + ' --prefix ' + obj_prefix + lane)
                log.debug(swift_list_cmd)
                # Get swift listing
                swift_list_cmd_output = subprocess.check_output(swift_list_cmd, shell=True)
                fastq_file_paths = filter(None, swift_list_cmd_output.rstrip('\n').split('\n'))
                # Make sure we got some files from the listing
                if(not fastq_file_paths):
                    log.error('Fastq files for ' + bid + ' could not be found on swift. BID '
                        + bid + ' will not be run.')
                    continue
                # If we have anything other than two fastq files, make a note
                if(len(fastq_file_paths) != 2):
                    log.warning('Unexpected number of fastq files found on swift for this lane')
                fastq_files = map(lambda x: os.path.basename(x), fastq_file_paths)
                
                # Attempt to download fastq files from swift
                try:
                    download_from_swift(container, obj_prefix)
                except Exception as e:
                    log.error('Swift download failed. BID ' + bid + ' will not be run.')
                    log.debug('Exception: ' + str(e))
                    continue
                
                # Make sure files were downloaded properly
                # TODO Maybe an md5 or something here to make sure all is well?
                # TODO I'm not too sure how necessary this is
                # TODO Should this give more than just a warning?
                if not (os.path.isfile(fastq_dir + '/' + fastq_files[0]) 
                    and os.path.isfile(fastq_dir + '/' + fastq_files[1])):
                    log.warning('Expected files don\'t actually exist')
                    log.debug('Dir listing: ' + str(os.listdir(fastq_dir)))
                
                # Setup logs dir
                log_dir = fastq_dir + '/logs'
                log.info('Creating logs directory at ' + log_dir)
                try:
                    subprocess.check_call('mkdir -p ' + log_dir, shell=True)
                except Exception as e:
                    log.error('Creating logs directory ' + log_dir + ' failed.')
                    log.debug('Exception: ' + str(e))
                    log.debug(traceback.format_exc().rstrip('\n'))
                
                # Change into fastq dir to run pipeline
                os.chdir(fastq_dir)
                log.info('Changed to directory ' + fastq_dir)
                
                # Run ATACseq pipeline
                try:
                    run_ATACseq_pipeline()
                except Exception as e:
                    log.error('ATACseq pipeline failed')
                    log.debug('Exception: ' + str(e))
                    log.debug(traceback.format_exc().rstrip('\n'))
                
                # Change back to working directory
                os.chdir(cwd)
                log.info('Changed to working directory')
                
                # Cleanup fastq files
                # TODO I'm not sure how I should do this yet, I'll revisit after
                # more of the pipeline itself is written
            
            # Run successful
            log.info('Run successful!')
            
            # Move log file into log_dir
            mv_log_cmd = 'mv ' + log_file_path + ' ' + log_dir
            log.info('Moving log file into log directory')
            try:
                subprocess.check_call(mv_log_cmd, shell=True)
            except Exception as e:
                log.warning('Could not move log file into log directory')
                log.debug('Exception: ' + str(e))
                log.debug(traceback.format_exc().rstrip('\n'))
            log.removeHandler(log_file)
            
            
            
            
# TODO Move log into appropriate folder
# TODO Add removehandler above
if __name__ == '__main__':
    main()
