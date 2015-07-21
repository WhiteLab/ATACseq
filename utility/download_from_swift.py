import sys
import subprocess
import traceback
import logging
sys.path.append('/home/ubuntu/src/ATACseq/utility')
from date_time import date_time

# Get logger
log = logging.getLogger('log')

def download_from_swift(container, obj):
    src_cmd = '. /home/ubuntu/.novarc; '
    swift_download_cmd = (src_cmd + 'swift -v download '
        + container + ' --skip-identical --prefix ' + obj)
    log.info('Attempting to run swift download for ' + container + ' -> ' + obj + '*')
    log.debug(swift_download_cmd)
    try:
        subprocess.check_call(swift_download_cmd, shell=True)
    except Exception:
        raise
    log.info('Swift download successful')

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple download module to get '
        + 'file from Swift. Can use prefix or whole object name.')
    parser.add_argument('-c', '--container', help='Swift container, i.e. PsychENCODE')
    parser.add_argument('-o', '--obj', help='Swift object name/prefix, i.e. RAW/2015-1234')
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    inputs = parser.parse_args()
    
    # Setup local logger
    logging.basicConfig(format=format_string, datefmt=datefmt_string, level=logging.DEBUG)
    
    try:
        download_from_swift(inputs.container, inputs.obj)
    except Exception as e:
        log.critical('Swift download failed')
        log.debug('Exception: ' + str(e))
        log.debug(traceback.format_exc().rstrip('\n'))
        sys.exit(1)

