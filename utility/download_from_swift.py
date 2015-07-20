import sys
import subprocess
import traceback
sys.path.append('/home/ubuntu/src/ATACseq/utility')
from date_time import date_time

def download_from_swift(container, obj):
    src_cmd = '. /home/ubuntu/.novarc; '
    swift_download_cmd = (src_cmd + 'swift -v download '
        + container + ' --skip-identical --prefix ' + obj)
    sys.stderr.write(date_time() + ': Attempting to run Swift download.\n')
    sys.stderr.write(swift_download_cmd + '\n')
    try:
        subprocess.check_output(swift_download_cmd, shell=True)
    except Exception:
        sys.stderr.write(date_time() + ': Download of ' + obj + ' from '
            + container + ' failed.\n')
        raise
    sys.stderr.write(date_time() + ': Swift download successful.')

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
    try:
        download_from_swift(inputs.container, inputs.obj)
    except Exception as e:
        sys.stderr.write('FATAL ERROR: ' + str(e) + '\n')
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

