import psutil
import platform
import json
import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, after_this_request, Response, render_template
from flask_caching import Cache
from flask_restful import Resource, Api
from flask_cors import CORS, cross_origin
from flask_compress import Compress
import conf
import constants
import pymysql.cursors
import time
from timeloop import Timeloop
import win32api
import time
from PIL import ImageTk, Image
import threading
from waitress import serve
import subprocess
import sys
import pyautogui
from camera_desktop import Camera
import ctypes
from datetime import datetime
pyautogui.FAILSAFE= False


app = Flask(__name__)
api = Api(app)
Compress(app)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
tl = Timeloop()
BASE_URL = '/api/v0/'
MASTER_URL = "https://tacpoint-master-001.adaptive-api.com/api/v0/"
now = datetime.now().isoformat()

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

@app.route(BASE_URL + 'rmm/screen', methods=['GET'])
def rmm_ScreenShare():
	return render_template('remote.html')

@app.route(BASE_URL + 'rmm/screen/video_feed')
def video_feed():
	return Response(gen(Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen(camera):
	while True:
		frame = camera.get_frame()
		yield (b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route(BASE_URL + 'rmm/screen/mouse', methods=['POST'])
def mouse_event():
	# co-ordinates of browser image event
	ex, ey = float(request.form.get('x')), float(request.form.get('y'))
	# size of browser image
	imx, imy = float(request.form.get('X')), float(request.form.get('Y'))
	# size of desktop
	dx, dy = pyautogui.size()
	# co-ordinates of desktop event
	x, y = dx*(ex/imx), dy*(ey/imy)
	# mouse event
	event = request.form.get('type')

	if event == 'click':
		pyautogui.click(x, y)
	elif event == 'dblclick':
		pyautogui.doubleClick(x, y)
	elif event == 'rightclick':
		pyautogui.click(x, y, button='right')

	return Response("success")


@app.route(BASE_URL + 'rmm/screen/keyboard', methods=['POST'])
def keyboard_event():
	# keyoard event
	event = request.form.get('type')
	print(event)
	if event == "text":
		text = request.form.get("text")
		pyautogui.typewrite(text)
	else:
		pyautogui.press(event)
	return Response("success")

@app.route(BASE_URL + 'cluster/join/<cluster_id>', methods=['GET'])
def joinCluster(cluster_id):
    con = open_connection()
    query = 'select * from clusters where cluster_id="{0}"'.format(cluster_id)
    try:
        cur = con.cursor()
        cur.execute(query)
        res = cur.fetchall()
    
    except Exception as error:
        print(error)
        return jsonify({'message': 'server error'})
    # host = 'localhost:4444'
    host = res[0]['cluster_host'] + ':' + str(res[0]['cluster_port'])
    print("Host: {0}".format(host))
    uri = 'http://' + host + '/api/v0/ep/join'
    print("Uri: {0}".format(uri))
    data = {"timestamp": datetime.now().isoformat(), "endpoint_id": conf.ep_id, "sysinfo": gatherSystemInfo()}
    r = requests.put(uri, json=data)
    print(r)
    return jsonify({'message': 'ok'})

class WinAlert(object):
    def __init__(self, msg, title):

        thread = threading.Thread(target=self.run, args=(msg, title))
        thread.daemon = True
        thread.start()

    def run(self, msg, title):
        win32api.MessageBox(0, msg, title, 0x00001000)

@app.route

@app.route(BASE_URL + "tasks/eset/scan", methods=['GET'])
def eset_ScanSystem():
    subprocess.Popen('"C:\Program Files\ESET\ESET Security\ecls.exe" /base-dir="C:\Program Files\ESET\ESET Security\Modules" /auto /aind /log-file=%APPDATA%\Adaptive\Tacpoint\scans\eset-scan-'+now+'.txt', shell=True)
    return jsonify({"message":"success"})

@app.route(BASE_URL + "tasks/lock-workstation", methods=['GET'])
def lock_Workstation():
    cmd='rundll32.exe user32.dll, LockWorkStation'
    subprocess.call(cmd)
    return jsonify({"message":"success"})


@app.route(BASE_URL + "tasks/win-alert", methods=['PUT'])
def winAlert():
    data = request.get_json()
    json_data = json.loads(data)
    print(json.dumps(json_data))
    title = json_data['title']
    msg = json_data['msg']
    @after_this_request
    def showMessage(response):
        try:
            alert = WinAlert(msg, title)
        except Exception as error:
            print(error)

        return response
        
    return jsonify({'message': 'ok'})

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
        print(res)
        if rec['data'] != '': doTask(res[0]['uri'], res[0]['method'], rec['data'])
        else: doTask(res[0]['uri'], res[0]['method'])
        query = 'update task_list set is_completed=1, time_completed="{0}" where task_id="{1}" and endpoint_id="{2}"'.format(datetime.now().isoformat(), rec['task_id'], conf.ep_id)
        try:
            cur = con.cursor()
            cur.execute(query)
            con.commit()
            cur.close()
        except Exception as error:
            print(error)
        
    return

def doTask(uri, method, data={}):
    con = open_connection()
    localhost = 'http://localhost:5000'
    if method == 'PUT':
        print('data>>>>>',data)
        r = requests.put(localhost + uri, json=data)
        print(r)
        return
    if method == 'GET':
        r = requests.get(localhost + uri)
        print(r)
        return


def healthCheck():
    con = open_connection()
    r1 = requests.get(MASTER_URL + 'db/ep_id/' + conf.ep_id)
    r1_res = r1.json()
    r1_data = r1_res['ep']
    r2 = requests.get(MASTER_URL + 'db/cluster_id/' + r1_data['cluster_id'])
    r2_res = r2.json()
    r2_data = r2_res['cluster']

    sysinfo = gatherSystemInfo()
    timestamp = datetime.now().isoformat()
    # host = 'localhost:4444'
    host = r2_data['cluster_host'] + ':' + str(r2_data['cluster_port'])
    json = {"timestamp": timestamp, "endpoint_id": conf.ep_id, "sysinfo": sysinfo}
    uri = 'https://' + host + '/v1/ep/healthcheck/' + conf.ep_id
    print('requrl>>>', uri)
    r = requests.put(uri, json=json)
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





tl.start(block=False)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    


