import subprocess
import os
import pathlib

def get_pods():
    path = pathlib.Path("logs/k8s_pods.log")
    if path.exists ():
        os.remove('logs/k8s_pods.log')

    f = open("logs/k8s_pods.log", "w+")
    subprocess.call('kubectl get pods --all-namespaces', shell=True, stdout=f)
    return