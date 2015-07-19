import sys
import json
import argparse
sys.path.append('/home/ubuntu/src/ATACseq/utility')
from setup_vm import setup_vm
from attach_cinder import attach_cinder
from date_time import date_time

def basic_node_setup(bid, vm_config, timeout):
    # Get VM config options from JSON file
    (vm_image_id, vm_flavor, vm_key
        cinder_snapshot_id, cinder_size,
        mount_sh_path, unmount_sh_path) = parse_config(vm_config)
    # Setup VM here
    try:
        vm_id, vm_ip = setup_vm(bid, vm_image_id, vm_flavor, vm_key, timeout)
        # VM is setup, attach cinder block
        attach_cinder(cinder_snapshot_id, vm_id, bid,
            cinder_size, vm_ip, timeout, sh_scripts_path)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)
    
    sys.stderr.write(date_time() + ': VM booted and cinder attached. VM generation successful.\n')
        
    
    
    
def parse_config(vm_config):
    config_data = json.loads(open(vm_config, 'r').read())
    return (config_data['vm_image']['id'],
        config_data['vm_image']['flavor'],
        config_data['vm_image']['key'],
        config_data['cinder_ref']['snapshot_id'],
        config_data['cinder_ref']['size'],
        config_data['sh_scripts']['mount'],
        condig_data['sh_scripts']['unmount']
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-id', '--BID', dest='bid', required=True,
        help='Project Bionimbus ID.')
    parser.add_argument('-c', '--config', dest='config_file', required=True,
        help='JSON config file with snapshot IDs and set-up parameters.')
    parser.add_argument('-t', '--timeout', default='600', type=int,
        help='Time to wait before giving up on spawning an image in seconds. Default is 600 seconds.')
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    inputs = parser.parse_args()
    
    bid = inputs.bid
    config_file = inputs.config_file
    timeout = inputs.timeout
    
    basic_node_setup(bid, config_file, timeout)
    
if __name__ == '__main__':
    main()
