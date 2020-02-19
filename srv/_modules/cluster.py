import errno
import os
import subprocess
import sys
import yaml

from shutil import copyfile

def storage_device_config():
    _pillar_path = '/opt/seagate/eos-prvsnr/pillar/components/cluster.sls'
    if not os.path.exists(_pillar_path):
        _pillar_path = '/opt/seagate/ees-prvsnr/pillar/components/cluster.sls'
        if not os.path.exists(_pillar_path):
            print("[ERROR   ] Cluster file {0} doesn't exist.".format(_pillar_path))
            raise FileNotFoundError(
                errno.ENOENT,
                os.strerror(errno.ENOENT),
                _pillar_path
            )
    
    if not os.path.exists(_pillar_path + '.bak'):
        copyfile(_pillar_path, _pillar_path + '.bak')

    _pillar_dict = dict()
    with open(_pillar_path, 'r') as fd:
        _pillar_dict = yaml.safe_load(fd)

    for node in _pillar_dict["cluster"]["node_list"]:
        if _pillar_dict["cluster"][node]["is_primary"]:
            cmd = "multipath -ll | grep prio=50 -B2|grep mpath|sort -k2.2 | awk '{ print $1 }'"
        else:
            cmd = "multipath -ll | grep prio=10 -B2|grep mpath|sort -k2.2 | awk '{ print $1 }'"
        
        device_list = subprocess.Popen([cmd],
                                        shell=True,
                                        stdout=subprocess.PIPE
                                    ).stdout.read().decode("utf-8").splitlines()
        
        if device_list == []:
            # Do nothing, probably a VM
            return True
        
        metadata_device = list()
        metadata_device.append(f"/dev/disk/by-id/dm-name-{device_list[0]}")
        _pillar_dict["cluster"][node]["storage"]["metadata_device"] = metadata_device
        data_device = list()
        data_device.append("/dev/disk/by-id/dm-name-mpath[" + ",".join(list(map(lambda x: x[5:], device_list[1:]))) + "]")
        _pillar_dict["cluster"][node]["storage"]["data_devices"] = data_device

    with open(_pillar_path, 'w') as fd:
        yaml.dump(
            _pillar_dict,
            stream=fd,
            default_flow_style = False,
            canonical=False,
            width=1,
            indent=4
        )

    return True