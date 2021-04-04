import subprocess
import os

def init_k8s():
    k8sconf_inp = 'br_netfilter'
    k8sconf = open("/etc/modules-load.d/k8s.conf", "w")
    k8sconf.write(k8sconf_inp)
    k8sconf.close()

    k8sconf2_inp = 'net.bridge.bridge-nf-call-iptables = 1 \r\nnet.bridge.bridge-nf-call-ip6tables = 1 \r\n'
    k8sconf2 = open("/etc/sysctl.d/k8s.conf","w")
    k8sconf2.write(k8sconf2_inp)
    subprocess.call('swapoff -a', shell=True)
    subprocess.call('hostnamectl set-hostname k8s-master', shell=True)
    subprocess.call('sysctl --system', shell=True)
    subprocess.call('apt update', shell=True)

    subprocess.call('DEBIAN_FRONTEND=noninteractive apt install -y apt-transport-https', shell=True)
    subprocess.call('apt install -y ca-certificates curl software-properties-common', shell=True)

    subprocess.call('ufw disable', shell=True)
    subprocess.call('sudo curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg', shell=True)
    subprocess.call('echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list', shell=True)
    subprocess.call('apt update', shell=True)
    subprocess.call('DEBIAN_FRONTEND=noninteractive apt install -y kubeadm kubelet kubectl', shell=True)
    subprocess.call('apt-mark hold kubelet kubeadm kubectl', shell=True)
    subprocess.call('kubeadm config images pull', shell=True)
    subprocess.call('kubeadm init --pod-network-cidr=10.244.0.0/16', shell=True)
    subprocess.call('mkdir -p $HOME/.kube', shell=True)
    subprocess.call('sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config', shell=True)
    subprocess.call('sudo chown $(id -u):$(id -g) $HOME/.kube/config', shell=True)
    subprocess.call('mkdir /root/k8s', shell=True)
    subprocess.call('cd /root/k8s', shell=True)
    subprocess.call('curl https://docs.projectcalico.org/manifests/calico.yaml -O', shell=True)
    subprocess.call('kubectl apply -f calico.yaml', shell=True)
