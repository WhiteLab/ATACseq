import sys
import subprocess
import re
sys.path.append('/home/ubuntu/src/ATACseq/utility')
from date_time import date_time

def get_cinder_show_attr(cinder_show_output, attr):
    '''Returns the desired attribute from nova show output'''
    for line in re.findall('(.*)\n', cinder_show_output):
        line = line.rstrip('\n')
        matched_line = re.match(r'\|\s+(\S+)\s+\|\s+(\S+)\s+\|', line)
        if matched_line:
            if matched_line.group(1) == attr:
                return matched_line.group(2)
    return None
    
def wait_until_status(status, status_verb, cinder_id, timeout):
    ''' Wait until a certain status is observed '''
    src_cmd = '. /home/ubuntu/.novarc; '
    sleep_time = 30
    sleep_cmd = 'sleep ' + str(sleep_time) + 's'
    elapsed_time = 0
    waiting_on_status = True
    while waiting_on_status:
        sys.stderr.write(date_time() + ': Sleeping ' + str(sleep_time) + 's.\n')
        subprocess.call(sleep_cmd, shell=True)
        elapsed_time += sleep_time
        if elapsed_time > int(timeout): # TODO I think we should delete the VM somehow, wait until ACTIVE
            raise Exception('FATAL ERROR: cinder still ' + status_verb 
                + 'ing as timeout of ' + str(timeout) 
                + 's was reached. Increase timeout and try again.\n')
        sys.stderr.write(date_time() + ': Checking success of cinder ' 
            + status_verb + '. '
            + str(elapsed_time) + ' seconds have passed.\n')
        cinder_show_cmd = src_cmd + 'cinder show ' + cinder_id
        cinder_show_cmd_output = subprocess.check_output(cinder_show_cmd, shell=True)
        cinder_status = get_cinder_show_attr(cinder_show_cmd_output, 'status')
        if cinder_status == status:
            waiting_on_status = False

def attach_cinder(snapshot_id, vm_id, bid, cinder_size, vm_ip, timeout, mount_sh_path):
    cinder_name = 'refs_' + str(bid)
    sys.stderr.write(date_time() + ': Creating cinder volume '
        + cinder_name + ' using snapshot ID '
        + snapshot_id + ' to VM with ID ' + vm_id + '\n')
        
    # Source .novarc command
    src_cmd = '. /home/ubuntu/.novarc; '
    
    # Build cinder create command
    cinder_create_cmd = (src_cmd + 'cinder create ' + str(cinder_size)
        + ' --snapshot-id ' + snapshot_id
        + ' --display-name ' + cinder_name)
    sys.stderr.write(cinder_create_cmd + '\n')
    cinder_create_output = subprocess.check_output(cinder_create_cmd, shell=True)
    
    # Get cinder id
    cinder_id = get_cinder_show_attr(cinder_create_output, 'id')
    
    # Check status of cinder every 30 seconds until finished spawning
    wait_until_status('available', 'boot', cinder_id, timeout)
    
    # Cinder is now booted, attach to VM
    sys.stderr.write(date_time() + ': Cinder create for ' + cinder_name
        + ' with ID ' + cinder_id + ' was successful. Attaching to VM.\n')
    volume_attach_cmd = src_cmd + 'nova volume-attach ' + vm_id + ' ' + cinder_id
    sys.stderr.write(volume_attach_cmd + '\n')
    subprocess.call(volume_attach_cmd, shell=True)
    
    # Make sure cinder attaches
    wait_until_status('in-use', 'attach', cinder_id, timeout)
    
    # Set mount point in VM
    sys.stderr.write(date_time() + ': Mounting volume in VM.\n')
    mount_cmd = ('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ubuntu@'
        + vm_ip + ' \"sh -s\" < ' + mount_sh_path + ' \"refs_'
        + bid + '\" exit;')
    sys.stderr.write(mount_cmd + '\n')
    subprocess.call(mount_cmd, shell=True)
    sys.stderr.write(date_time() + ': Cinder successfully mounted.\n')

if __name__ == "__main__":
    import argparse

    # TODO add description
    parser = argparse.ArgumentParser()
    parser.add_argument('-sid', '--snapshot-id', dest='snapshot_id', 
        help='ID of snapshot.  Use cinder to find')
    parser.add_argument('-vid', '--vm-id', dest='vm_id', 
        help='Virtual machine id.  Use Nova to find')
    parser.add_argument('-id', '--BID', dest='bid', help='Bionimbpus project id')
    parser.add_argument('-s', '--cinder-size', dest='cinder_size', 
        help='Cinder reference size.  Recommended value 200 (in GB)')
    parser.add_argument('-ip', '--vm-ip', dest='vm_ip',help='VM IP address')
    parser.add_argument('-t', '--timeout', dest='timeout',
        help='Wait time before giving up on spawning an image. '
        + 'Recommended value 300 (in seconds)')
    parser.add_argument('-m', '--mount-sh-path', dest='mount_sh_path',
        help='Path to the mount.sh script on the VM')
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    inputs = parser.parse_args()
    snapshot_id = inputs.snapshot_id
    vm_id = inputs.vm_id
    bid = inputs.bid
    cinder_size = inputs.cinder_size
    timeout = inputs.timeout
    vm_ip = inputs.vm_ip
    mount_sh_path = inputs.mount_sh_path
    attach_cinder(snapshot_id, vm_id, bid, cinder_size, vm_ip, timeout, mount_sh_path)

