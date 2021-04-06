import subprocess
import os

 
def k8s_apply_conf():
    subprocess.call('cd /root/', shell=True)
    subprocess.call('kubectl apply -f k8s.conf', shell=True)
    subprocess.call('rm -rf k8s.conf', shell=True)
    return