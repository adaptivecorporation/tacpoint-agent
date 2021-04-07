import subprocess
import os

 
def k8s_apply_conf():
    subprocess.call('ls')
    subprocess.call('kubectl apply -f uploads/k8s.yml', shell=True)
    subprocess.call('rm -rf k8s.yml', shell=True)
    return


def cli(command):
    subprocess.call(command, shell=True)
    return