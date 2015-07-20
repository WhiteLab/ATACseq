import sys
import os
import subprocess
import traceback
sys.path.append('/home/ubuntu/src/ATACseq/utility')
from date_time import date_time

def parse_config(config_file):
    

def main():
    parser = argparse.ArgumentParser(description='Handles running pipeline.')
    # TODO come up with more meaningful flags
    parser.add_argument('-f', '--file', help='File with Bionimbus ID, seqtype, and '
        + 'sample lane list.')
    parser.add_argument('-j', '--json', help='JSON config file with tools, references, '
        + 'data storage locations.')
    parser.add_argument('-m', '--mount', help='Reference mount drive location.')
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    inputs = parser.parse_args()
    bid_file_path = inputs.file
    config_file = inputs.json
    ref_mnt = inputs.mount
    
    # Open bid file, read line by line
    with open(bid_file_path, 'r') as bid_file:
        for line in bid_file:
            line = line.rstrip('\n')
            # Get run info from bid file
            bid, seqtype, lane_csv = line.split('\t')
            
            # Set and create, if necessary, a working directory
            cwd = ref_mnt + '/SCRATCH'
            if os.path.isdir(cwd) == False:
                sucprocess.call('mkdir -p ' + cwd, shell=True)
            
            # Change to working directory
            try:
                os.chdir(cwd)
            except Exception as e:
                sys.stderr.write(date_time() + ': Creating directory for ' + bid
                    + ' failed. Ensure the correct machine is being used for '
                    + 'this sample set.\n')
                sys.stderr.write('FATAL ERROR: ' + str(e) + '\n')
                traceback.print_exc(file=sys.stderr)
                sys.exit(1)
            
            

if __name__ == '__main__':
    main()
