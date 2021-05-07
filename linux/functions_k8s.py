import subprocess
import os
import pathlib

def get_pods():
    path = pathlib.Path("./logs/k8s_pods.log")
    if path.exists ():
        os.remove('./logs/k8s_pods.log')

    with open("./logs/k8s_pods.log", "w+") as f:
        subprocess.call('kubectl get pods --all-namespaces', shell=True, stdout=f)
        return f.text