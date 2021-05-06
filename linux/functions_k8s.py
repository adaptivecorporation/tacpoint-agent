import subprocess
import os

def get_pods():
    try:
        os.remove('./logs/k8s_pods.log')
        
    except Exception as error:
        pass

    f = open("./logs/k8s_pods.log", "w")
    subprocess.call('kubectl get pods --all-namespaces', shell=True, stdout=f)
    return f.text