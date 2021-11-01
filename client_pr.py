import socket
import getpass
import re
import threading
import os

DEF_HOST = '127.0.0.1'  # The server's hostname or IP address
DEF_PORT = 65432        # The port used by the server
max = 100000
tokenfile = 'token.txt'


def user_conf():
    ip = re.search(r'^\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}$', getpass.getpass(
        prompt='enter ip you want to connect: '))
    ip = ip.group() if ip else DEF_HOST
    while True:
        user_port = getpass.getpass(
            prompt="Enter port you want to use: ", stream=None)
        try:
            user_port = int(
                user_port) if user_port != '' else DEF_PORT
            user_port = user_port if 1 < user_port < 65537 else DEF_PORT
            break
        except:
            continue
    return ip, user_port


def receive(conn):
    while True:
        try:
            message = conn.recv(1024).decode()
            print(message)
        except:
            break


def token():
    if tokenfile in os.listdir(os.getcwd()):
        with open(tokenfile, 'r', encoding='utf-8') as ss:
            t = ss.read()
            return t if t else 'no token'
    else:
        a = open(tokenfile, 'w')
        a.close()
        return 'no token'


def write_token(line):
    with open(tokenfile, 'w', encoding='utf-8') as file:
        file.write(line)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    ip, port = user_conf()
    try:
        s.connect((ip, port))  # connect to server
        print('connection with server was successfull')
    except:
        print('Connection can not be complete')
        exit()
    while True:
        sign = s.recv(1024).decode()
        if 'name' in sign:
            s.send(input('Enter your name: ').encode())
        elif 'password' in sign:
            name = sign.split(',')[1]
            s.send(input(f'Enter your password, {name}: ').encode())
        elif 'token' in sign:
            tk = token()
            s.send(tk.encode())
        else:
            name = sign.split(',')[1]
            t = sign.split(',')[2] if len(sign.split(',')) > 2 else False
            if t:
                write_token(t)
            break
    print('----------enter for exit----------')
    data = s.recv(max).decode()
    if data == 'no messages':
        pass
    else:
        data = ''.join([i.lstrip()
                        for i in re.split(rf'{name}[:]', data)])[:-1]
        print(data)
    a = threading.Thread(target=receive, args=(s,))
    a.start()
    while True:
        text = str(input())
        if not text:
            break
        s.send(text.encode())
