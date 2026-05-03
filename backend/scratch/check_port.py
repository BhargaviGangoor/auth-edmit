import socket

def check_port(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            s.connect((host, port))
            return True
        except:
            return False

if __name__ == "__main__":
    if check_port('127.0.0.1', 5432):
        print("Port 5432 is open on localhost")
    else:
        print("Port 5432 is closed on localhost")
