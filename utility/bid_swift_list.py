import sys
import subprocess
sys.path.append('/home/ubuntu/src/ATACseq/utility')
from date_time import date_time

def bid_swift_list(container, obj, bid_list_file_path):
    src_cmd = '. /home/ubuntu/.novarc'
    with open(bid_list_file_path, 'r') as bid_list_file:
        for bid in bid_list_file:
            bid = bid.rstrip('\n')
            sys.stderr.write(date_time() + ': Executing swift list.\n')
            swift_list_cmd = (src_cmd + 'swift list '
                + container + ' --prefix '
                + obj + '/' + bid + '/')
            sys.stderr.write(swift_list_cmd + '\n')
            
# TODO This script makes no sense to me
