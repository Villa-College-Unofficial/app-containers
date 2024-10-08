from modules.container import Container
import socket
import subprocess
import threading

# Deprecated: Not used at the moment
class AppProxy:

    cont: Container = None
    http_proxy: subprocess.Popen = None
    http_port: int = None

    def __init__(self, cont:Container):
        self.cont = cont
        self.remote_addr = cont.docker_container.attrs['NetworkSettings']['IPAddress']
        self.remote_port = 8006
        self.listen = True
    
    def socat(self):
        _sock = socket.socket()
        _sock.bind(('', 0))
        self.http_port = int(_sock.getsockname()[1])
        self.http_proxy = subprocess.Popen(["socat", f"TCP-LISTEN:{self.http_port},fork,reuseaddr", f"TCP:{self.remote_addr}:8006"])
        print(f"listenening on '{self.http_port}'")

    def start(self):
        self.socat()

    def stop(self):
        self.http_proxy.kill()

    def __del__(self):
        self.http_proxy.kill()