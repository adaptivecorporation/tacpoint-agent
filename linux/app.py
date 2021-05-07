import psutil
import platform
import json
import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, after_this_request
from flask_caching import Cache
from flask_restful import Resource, Api
from flask_cors import CORS, cross_origin
from flask_compress import Compress
import conf
import constants
import pymysql.cursors
import time
from timeloop import Timeloop
import installers_k8s
import time
import functions
import os
import subprocess
import threading
from functions_k8s import get_pods
app = Flask(__name__)
api = Api(app)
Compress(app)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
UPLOAD_FOLDER = './uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
tl = Timeloop()
BASE_URL = '/api/v0/'


def open_connection():
    try:
        con = pymysql.connect(host=constants.DB_HOST, user=constants.DB_USER, password=constants.DB_PASSWORD, database=constants.DB_NAME, cursorclass=pymysql.cursors.DictCursor)

    except Exception as error:
        print(error)
    return con

def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


def gatherSystemInfo():
    uname = platform.uname()
    system = uname.system
    hostname = uname.node
    os_release = uname.release
    os_ver = uname.version
    machine = uname.machine
    processor = uname.processor
    boot_timestamp = psutil.boot_time()
    cpu_phy_cores = psutil.cpu_count(logical=False)
    cpu_freq = psutil.cpu_freq()
    cpu_usage = []
    for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
        app = {"core":i,"percentage":percentage}
        cpu_usage.append(app)
    svmem = psutil.virtual_memory()
    mem_total = get_size(svmem.total)
    mem_available = get_size(svmem.available)
    mem_used = get_size(svmem.used)
    mem_percentage = svmem.percent
    swap = psutil.swap_memory()
    swap_total = get_size(swap.total)
    swap_free = get_size(swap.free)
    swap_used = get_size(swap.used)
    swap_percentage = swap.percent
    partitions = psutil.disk_partitions()
    partition_arr = []
    for partition in partitions:
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
            disk_io = psutil.disk_io_counters()
            app = {"device": partition.device, "mountpoint": partition.mountpoint, "file_system_type": partition.fstype, "partition_total_size": get_size(partition_usage.total), "partition_used": get_size(partition_usage.used), "partition_free": get_size(partition_usage.free), "percentage_used": partition_usage.percent, "total read":get_size(disk_io.read_bytes), "total_write":get_size(disk_io.write_bytes)}
            partition_arr.append(app)
        except PermissionError:
            # this can be catched due to the disk that
            # isn't ready
            continue
    
    network_arr = []
    if_addrs = psutil.net_if_addrs()
    for interface_name, interface_addresses in if_addrs.items():
        for address in interface_addresses:
            if_family = address.family
            if_name = interface_name
            if_addr = address.address
            if_netmask = address.netmask
            if_broadcastip = address.broadcast
            if str(address.family) == 'AddressFamily.AF_PACKET': if_mac = address.address
            else: if_mac = ''
            if_broadcastmac = address.broadcast
            net_io = psutil.net_io_counters()
            app = {"if_family": if_family, "if_name": if_name, "if_addr": if_addr, "if_netmask": if_netmask, "if_broadcastip": if_broadcastip, "if_mac": if_mac, "if_broadcastmac": if_broadcastmac, "total_bytes_sent": get_size(net_io.bytes_sent), "total_bytes_recieved": get_size(net_io.bytes_recv)}
            network_arr.append(app)

    response = {"system": system, "hostname": hostname, "os_release": os_release, "os_ver": os_ver, "machine": machine, "proc": processor, "boot_timestamp": boot_timestamp, "cpu_phy_cores": cpu_phy_cores, "cpu_freq": cpu_freq, "cpu_usage": cpu_usage, "mem_total": mem_total, "mem_available": mem_available, "mem_used": mem_used, "mem_percentage": mem_percentage, "swap_total": swap_total, "swap_free": swap_free, "swap_used": swap_used, "swap_percentage": swap_percentage, "partitions": partition_arr, "network": network_arr}
    return response

@tl.job(interval=timedelta(seconds=60))
def checkIn():
    healthCheck()
    timestamp = datetime.now().isoformat()
    print('{0}: Running healthcheck'.format(timestamp))
    return

@app.route(BASE_URL + "sysinfo", methods=['GET'])
def getSysInfo_API():
    return jsonify({"sys_info": gatherSystemInfo()})

@app.route(BASE_URL + 'cluster/join/<cluster_id>', methods=['GET'])
def joinCluster(cluster_id):
    r = requests.get('https://tacpoint-master-001.adaptive-api.com/api/v0/cluster/uri/' + cluster_id)
    r_json = r.json()
    
    # host = 'localhost:4444'
    host = r_json['uri']
    print("Host: {0}".format(host))
    uri = host
    print("Uri: {0}".format(uri))
    data = {"timestamp": datetime.now().isoformat(), "endpoint_id": conf.ep_id, "sysinfo": gatherSystemInfo()}
    r = requests.put(uri, json=data, verify=False)
    print(r)
    return jsonify({'message': 'ok'})

@app.route(BASE_URL + "tasks/system/swapoff", methods=['GET'])
def system_SwapOff():
    subprocess.call('sudo swapoff -a', shell=True)
    return jsonify({"message":"success"})

@app.route(BASE_URL + "k8s/pods/get", methods=['GET'])
def get_pods_k8s():
    pods = get_pods()
    f = open('logs/k8s_pods.log', 'r')
    return jsonify({'pods': f.read()})

@app.route(BASE_URL + "tasks/k8s/init", methods=['GET'])
def initk8s():
    @after_this_request
    def run_initk8s(response):
        installers_k8s.init_k8s()
        return response
    return jsonify({'message':'Cluster initilizing.'})

@app.route(BASE_URL + "tasks/k8s/apply", methods=['POST'])
def apply_k8s():
    con = open_connection()
    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file provided')
            return jsonify({'message': 'no file provided!'})
        file = request.files['file']
        if file.filename == '':
            return jsonify({'message': 'no selected file!'})
        if file:
            print('Processing file...')
            filename = 'k8s.yml'
            uploaded_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(uploaded_file)
            functions.k8s_apply_conf()
            return jsonify({'message': '200'})

def doTasks(arr):
    con = open_connection()
    for rec in arr:
        query = 'select * from tasks where task_id="{0}"'.format(rec['task'])
        try:
            cur = con.cursor()
            cur.execute(query)
            res = cur.fetchall()
        except Exception as error:
            print(error)
            return jsonify({'message': 'error'})

        doTask(res[0]['uri'], res[0]['method'], rec['data'])
        query = 'update task_list set is_completed=1, time_completed="{0}" where task_id="{1}" and endpoint_id="{2}"'.format(datetime.now().isoformat(), rec['task_id'], conf.ep_id)
        try:
            cur = con.cursor()
            cur.execute(query)
            con.commit()
            cur.close()
        except Exception as error:
            print(error)
        
    return

def doTask(uri, method, data):
    con = open_connection()
    localhost = 'http://localhost:5000'
    if method == 'PUT':
        print('data>>>>>',data)
        data_ = data.replace("'",'"')
        r = requests.put(localhost + uri, json=data)
        print(r)
        return
    if method == 'GET':
        r = requests.get(localhost + uri)
        print(r)
        return


def healthCheck():
    con = open_connection()
    query = 'select * from endpoints where endpoint_id="{0}"'.format(conf.ep_id)
    
    try:
        cur = con.cursor()
        cur.execute(query)
        res = cur.fetchall()
        q2 = 'select * from clusters where cluster_id="{0}"'.format(res[0]['cluster_id'])
        cur.execute(q2)
        q2res = cur.fetchall()

    except Exception as error:
        print(error)
        return 500
    

    sysinfo = gatherSystemInfo()
    timestamp = datetime.now().isoformat()
    # host = 'localhost:4444'
    host = q2res[0]['cluster_host'] + ':' + str(q2res[0]['cluster_port'])
    json = {"timestamp": timestamp, "endpoint_id": conf.ep_id, "sysinfo": sysinfo}
    uri = 'https://' + host + '/v1/ep/healthcheck/' + conf.ep_id
    print('requrl>>>', uri)
    r = requests.put(uri, json=json, verify=False)
    print(r)
    resp = r.json()
    if 'tasks' in resp: tasks = resp['tasks']
    else: tasks = []
    taskArr = []
    for rec in tasks:
        taskArr.append(rec)
    print('tasks', taskArr)
    if len(taskArr) > 0: doTasks(taskArr)
    return 200


@app.route(BASE_URL + 'shell/cli', methods=['PUT'])
def api_cli():
    data = request.get_json()
    cmd = data['cmd']
    functions.cli(cmd)
    return jsonify({'message': 'ok'}),200


tl.start(block=False)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5150)
    


