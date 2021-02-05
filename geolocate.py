import subprocess
import re
import threading
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import cartopy.crs as ccrs
import time
import requests
import json
import sys, os
import builtins
import socket

"""
    https://stackoverflow.com/questions/14986490/python-change-sys-stdout-print-to-custom-print-function
    On my mac, FuncAnimation causes a bunch of repeated diagnostic errors into stderr (not an Exception, mind you). 
    This is a hacky solution.
"""

class FilterPrint():
    def __init__(self):
        self._old_stderrr = sys.stderr

    def write(self, text):
        if text == "IllegalArgumentException: Argument must be Polygonal or LinearRing":
            return
        self._old_stderr.write(text)

    def flush(self):
        self.old_stderr.flush()

sys.stderr = FilterPrint()


try:
    url = sys.argv[1]
except IndexError:
    url = "www.u-tokyo.ac.jp"

target_ip = socket.gethostbyname(url)

lat_lst = []
lon_lst = []

def get_coords_worker(ip, prev_thread):
    global lat_lst, lon_lst
    response = requests.get(f"http://ip-api.com/json/{ip}").json()

    if prev_thread is not None:
        prev_thread.join() # make sure coordinates are displayed in order
    
    if response['status'] == 'fail':
        return
        
    lat, lon = response['lat'], response['lon']
    
    lat_lst.append(lat)
    lon_lst.append(lon)
    return lat, lon

def plot_coords():
    sp = subprocess.Popen(f"traceroute {url}", shell=True, stdout=subprocess.PIPE)
    threads = []
    thread_ = None
    fail_counter = 0


    while True:
        if sp.poll() is not None or fail_counter >= 3:
            break
        line = sp.stdout.readline().decode('utf-8')

        
        re_search = re.search('\(((?:\d+\.?)+)\)', line)
        if re_search is None:
            fail_counter += 1
            continue
        fail_counter = 0
        ip = re_search.group(1)

        if ip == target_ip:
            break

        t = threading.Thread(target=get_coords_worker, args=[ip, thread_], daemon=True)
        t.start()
        thread_ = t
        threads.append(t)

    
    print('done')
    
    anim.event_source.stop()


class LowerThresholdGeodetic(ccrs.Geodetic): # make lines look smoother

    @property
    def threshold(self):
        return 1e3
        


fig = plt.figure()

ax = plt.axes(projection=ccrs.Robinson())
ax.stock_img()
line, = ax.plot([], [], c='black', marker='o', lw=0.5, markersize=2, transform=LowerThresholdGeodetic())

def init():
    line.set_data([], [])
    return line,




def animate(_):
    line.set_data(lon_lst, lat_lst)
    return line,

    
t = threading.Thread(target=plot_coords, daemon=True)
t.start()

anim = FuncAnimation(fig, animate, init_func=init, save_count=600)

#anim.save('japan.gif',writer='imagemagick',fps=20) # use imagemagick to crop

plt.show()





