import os
import re
import multiprocessing as mp
from time import time

def combine_libraries(lib_dir):
    libraries = os.listdir(lib_dir)
    for lib in libraries:
        extra_re = re.compile(r'.extra')
        extra = extra_re.search(lib)
        if extra:
            print 'cat ' + lib.replace(extra.group(), '') + ' ' + lib + ' > ' + extra_re.sub('.combined', lib)
        
if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='Combine extra library resolution if 40M reads not met.')
    parser.add_argument('-d', '--dir', help='Directory containing fastq files.')
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    inputs = parser.parse_args()
    lib_dir = inputs.dir
    begin = time()
    combine_libraries(lib_dir)
    print 'elapsed time: ' + str(time() - begin) + ' seconds'
