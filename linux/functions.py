import subprocess
import os

 
def k8s_apply_conf():
    subprocess.call('ls')
    subprocess.call('kubectl apply -f uploads/k8s.conf', shell=True)
    subprocess.call('rm -rf k8s.conf', shell=True)
    return