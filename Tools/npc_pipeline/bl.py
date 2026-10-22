"""Send a Python file to the live Blender add-on (port 9876) and print the result. Usage: python bl.py code.py"""
import socket, json, sys
code = open(sys.argv[1], encoding='utf-8').read()
s = socket.create_connection(('127.0.0.1', 9876), timeout=600)
s.sendall(json.dumps({"type": "execute_code", "params": {"code": code}}).encode())
buf = b''
while True:
    buf += s.recv(65536)
    try:
        r = json.loads(buf); break
    except ValueError:
        continue
print(r.get('status'), r.get('message') or '')
print(r.get('result', ''))
