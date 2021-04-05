import subprocess
import os
import json

def init_k8s():
    subprocess.call('timedatectl set-timezone America/New_York', shell=True)
    subprocess.call('timedatectl set-ntp off', shell=True)
    k8sconf_inp = 'overlay \r\nbr_netfilter'
    k8sconf = open("/etc/modules-load.d/k8s.conf", "w")
    k8sconf.write(k8sconf_inp)
    k8sconf.close()

    k8sconf2_inp = 'net.bridge.bridge-nf-call-iptables = 1\r\nnet.ipv4.ip_forward = 1\r\nnet.bridge.bridge-nf-call-ip6tables = 1'
    k8sconf2 = open("/etc/sysctl.d/k8s.conf","w")
    k8sconf2.write(k8sconf2_inp)
    k8sconf3_inp = "net.bridge.bridge-nf-call-iptables = 1"
    k8sconf3 = open("/etc/sysctl.conf", "w")
    k8sconf3.write(k8sconf3_inp)
    subprocess.call('mkdir /etc/docker', shell=True)
    subprocess.call('swapoff -a', shell=True)
    subprocess.call('hostnamectl set-hostname k8s-master', shell=True)
    subprocess.call('sysctl --system', shell=True)
    subprocess.call('apt update', shell=True)

    subprocess.call('DEBIAN_FRONTEND=noninteractive apt install -y apt-transport-https', shell=True)
    subprocess.call('DEBIAN_FRONTEND=noninteractive apt install -y ca-certificates curl software-properties-common', shell=True)
    subprocess.call('curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -', shell=True)
    subprocess.call('sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"', shell=True)
    subprocess.call('apt update', shell=True)
    subprocess.call('apt-cache policy docker-ce', shell=True)
    subprocess.call('DEBIAN_FRONTEND=noninteractive sudo apt-get remove docker docker-engine docker.io containerd runc -y', shell=True)
    subprocess.call('DEBIAN_FRONTEND=noninteractive sudo apt-get -y purge docker-ce docker-ce-cli containerd.io', shell=True)
    subprocess.call('DEBIAN_FRONTEND=noninteractive sudo apt-get install docker-ce docker-ce-cli containerd.io -y', shell=True)
    subprocess.call('systemctl enable docker --now', shell=True)
    subprocess.call('systemctl restart docker', shell=True)
    
    # dockerconf1_inp = {
    #                 "exec-opts": ["native.cgroupdriver=systemd"],
    #                 "log-driver": "json-file",
    #                 "log-opts": {
    #                     "max-size": "100m"
    #                 },
    #                 "storage-driver": "overlay2"
    #                 }
    # subprocess.call('echo "{0}" >> /etc/docker/daemon.json'.format(dockerconf1_inp), shell=True)
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

