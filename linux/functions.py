import subprocess
import os

 
 def k8s_apply_conf(conf):
    subprocess.call('cd $HOME', shell=True)
    subprocess.call('echo "'+conf+'" > k8s.conf', shell=True)
    subprocess.call('kubectl apply -f k8s.conf', shell=True)
    subprocess.call('rm -rf k8s.conf', shell=True)
    return