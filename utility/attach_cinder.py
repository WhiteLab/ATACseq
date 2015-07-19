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

def attach_cinder(snapshot_id, vm_id, bid, size, vm_ip, timeout, mount_sh_path):
    cinder_name = 'refs_' + str(bid)
    sys.stderr.write(date_time() + ': Creating cinder volume '
        + cinder_name + ' using snapshot ID '
        + snapshot_id + ' to VM with ID ' + vm_id + '\n')
        
    # Source .novarc command
    src_cmd = '. /home/ubuntu/.novarc;'
    
    # Build cinder create command
    cinder_create_cmd = (src_cmd + 'cinder create ' + str(size)
        + ' --snapshot-id ' + snapshot_id
        + ' --display-name ' + cinder_name)
    cinder_create_ouput = subprocess.check_output(cinder_create_cmd, shell=True)
    
    # Get cinder id
    cinder_id = get_cinder_show_attr(cinder_create_output, 'id')
    
    # Check status of cinder every 30 seconds until finished spawning
    sleep_time = 30
    sleep_cmd = 'sleep ' + str(sleep_time) + 's'
    elapsed_time = 0
    cinder_still_booting = True
    cinder_show_cmd = src_cmd + 'cinder show ' + cinder_id
    
    # TODO This while block looks awfully similar to the while block below
    while cinder_still_booting:
        sys.stderr.write(date_time() + ': Sleeping ' + str(sleep_time) + 's.\n')
        subprocess.call(sleep_cmd, shell=True)
        elapsed_time += sleep_time
        if elapsed_time > int(timeout): # TODO I think we should delete the VM somehow, wait until ACTIVE
            raise Exception('FATAL ERROR: cinder still booting as timeout of ' + str(timeout) 
                + 's was reached. Increase timeout and try again.\n')
        sys.stderr.write(date_time() + ': Checking success of cinder boot. '
            + str(elapsed_time) + ' seconds have passed.\n')
        cinder_show_cmd_output = subprocess.check_output(cinder_show_cmd, shell=True)
        cinder_status = get_cinder_show_attr(cinder_show_cmd_output, 'status')
        if cinder_status == 'available':
            cinder_still_booting = False
            #cinder_ip = get_cinder_show_attr(cinder_show_cmd_output, 'private_network')
    
    # Cinder is now booted, attach to VM
    sys.stderr.write(date_time() + ': Cinder create for ' + cinder_name
        + ' with ID ' + cinder_id + ' was successful. Attaching to VM.\n')
    volume_attach_cmd = src_cmd + 'nova volume-attach ' + vm_id + ' ' + cinder_id
    sys.stderr.write(date_time() + volume_attach_cmd + '\n')
    subprocess.call(volume_attach_cmd, shell=True)
    
    # Make sure cinder attaches
    elapsed_time = 0
    cinder_still_attaching = True
    while cinder_still_attaching:
        sys.stderr.write(date_time() + ': Sleeping ' + str(sleep_time) + 's.\n')
        subprocess.call(sleep_cmd, shell=True)
        elapsed_time += sleep_time
        if elapsed_time > int(timeout): # TODO I think we should delete the VM somehow, wait until ACTIVE
            raise Exception('FATAL ERROR: cinder still attaching as timeout of ' + str(timeout) 
                + 's was reached. Increase timeout and try again.\n')
        sys.stderr.write(date_time() + ': Checking success of cinder attach. '
            + str(elapsed_time) + ' seconds have passed.\n')
        cinder_show_cmd_output = subprocess.check_output(cinder_show_cmd, shell=True)
        cinder_status = get_cinder_show_attr(cinder_show_cmd_output, 'status')
        if cinder_status == 'available':
            cinder_still_attaching = False
    
    sys.stderr.write(date_time() + ': Mounting volume in VM.\n')
    sys.stderr.write(mount_cmd + '\n')
    mount_cmd = ('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ubuntu@'
        + vm_ip + ' \"sh -s\" < ' + mount_sh_path + ' \"refs_'
        + bid + '\" exit;')
    subprocess.call(mount_cmd, shell=True)
    
    
