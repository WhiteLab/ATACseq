import sys
import subprocess
import re
sys.path.append('/home/ubuntu/src/ATACseq/utility')
from date_time import date_time
    
def get_nova_show_attr(nova_show_output, attr):
    '''Returns the desired attribute from nova show output'''
    for line in re.findall('(.*)\n', nova_show_output):
        # The replace() is in there because for some dumbass reason
        # the 'private network' property contains a space, and not an
        # underscore like the rest of the properties
        line = line.rstrip('\n').replace('private network', 'private_network')
        matched_line = re.match(r'\|\s+(\S+)\s+\|\s+(\S+)\s+\|', line)
        if matched_line:
            if matched_line.group(1) == attr:
                return matched_line.group(2)
    return None

def setup_vm(bid, image, flavor, key, timeout):
    sys.stderr.write(date_time() + ': Starting VM QC for sample set ' + str(bid) + '.\n')
    
    # Source .novarc command
    src_cmd = '. /home/ubuntu/.novarc;'
    
    # Build nova boot command
    vm_name = 'vm_pipe_' + str(bid)
    nova_boot_cmd = ('nova boot ' + vm_name + ' --image ' + image
        + ' --flavor ' + str(flavor) + ' --key-name ' + key)
    sys.stderr.write(date_time() + ': Booting up VM.\n' + nova_boot_cmd + '\n')
    nova_boot_cmd_output = subprocess.check_output(nova_boot_cmd, shell=True)
    
    # Get ID of VM in the event another has the same display name
    vm_id = get_nova_show_attr(nova_boot_cmd_output, 'id')
    
    # Check status of VM every 30 seconds until finished spawning
    sleep_time = 30
    sleep_cmd = 'sleep ' + str(sleep_time) + 's'
    elapsed_time = 0
    vm_still_booting = True
    nova_show_cmd = src_cmd + 'nova show ' + vm_id
    
    while vm_still_booting:
        sys.stderr.write(date_time() + ': Sleeping ' + str(sleep_time) + 's.\n')
        subprocess.call(sleep_cmd, shell=True)
        elapsed_time += sleep_time
        if elapsed_time > int(timeout): # TODO I think we should delete the VM somehow, wait until ACTIVE
            raise Exception('FATAL ERROR: VM still booting as timeout of ' + str(timeout) 
                + 's was reached. Increase timeout and try again.\n')
        sys.stderr.write(date_time() + ': Checking success of VM boot. '
            + str(elapsed_time) + ' seconds have passed.\n')
        nova_show_cmd_output = subprocess.check_output(nova_show_cmd, shell=True)
        vm_status = get_nova_show_attr(nova_show_cmd_output, 'status')
        if vm_status == 'ACTIVE':
            vm_still_booting = False
            vm_ip = get_nova_show_attr(nova_show_cmd_output, 'private_network')
        if vm_status == 'ERROR':
            raise Exception('FATAL ERROR: VM boot produced ERROR for ' + vm_name
                + '. Check connection settings and try again.\n')
    
    # VM has now booted up, transfer .novarc to new VM
    sys.stderr.write(date_time() + ': VM booted!\n')
    sleep_cmd = 'sleep 60s'
    sys.stderr.write(date_time() + ': Pausing 60s to give VM a chance to initialize.\n')
    subprocess.call(sleep_cmd, shell=True)  # TODO should we have a more robust check?
    rsync_nova_var_cmd = ('ssh-keyscan ' + vm_ip
        + ' >> ~/.ssh/known_hosts;rsync /home/ubuntu/.novarc ubuntu@'
        + vm_ip + ':/home/ubuntu')
    sys.stderr.write(date_time() + ': Copying openstack variables to VM\n'
        + rsync_nova_var_cmd + '\n')
    subprocess.call(rsync_nova_var_cmd, shell=True)
    sys.stderr.write(date_time() + ': VM setup for ' + vm_name
        + ' with IP address ' + vm_ip
        + ' with ID ' + vm_id + ' was successful.\n')
    
    # Return VM information
    return [vm_id, vm_ip]
    
if __name__ == '__main__':
    import argparse
    
    # TODO add description
    parser = argparse.ArgumentParser()
    parser.add_argument('-id','--BID',dest='bid',help='Project Bionimbus ID.')
    parser.add_argument('-im','--image',help='Image ID to spawn.')
    parser.add_argument('-t','--timeout', default='600', type=int,
        help='Wait time before giving up on spawning an image. Recommended value 300 (in seconds)')
    parser.add_argument('-f','--flavor',help='Image \"flavor\" to spawn.')
    parser.add_argument('-k','--key',help='Image key-pair to use.')
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
        
    inputs = parser.parse_args()
    bid = inputs.bid
    image = inputs.image
    flavor = inputs.flavor
    key = inputs.key
    timeout = inputs.timeout
    
    try:
        vm_vars = setup_vm(bid, image, flavor, key, timeout)
        print 'vm_vars: ' + str(vm_vars)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)

