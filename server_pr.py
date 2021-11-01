import os
import socket
import getpass
import csv
import threading
import datetime


class Server():
    listen_flag = True
    key = 'sglypa)'
    threadlist = []
    history = 'history.txt'
    logfile = 'log.txt'
    usernames = []
    log_text = {1: 'server is starting', 2: 'port is listened',
                3: 'connection was successfull', 4: 'server got data',
                5: 'client was disconnected', 6: 'server was turned off',
                7: 'server changed port', 8: 'new client', 9: 'message',
                10: 'pause', 11: 'show logs', 12: 'clear fileident'}
    Def_HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
    Def_PORT = 65432    # Port to listen on (non-privileged ports are > 1023)
    commands = ['listen', 'off', 'pause',
                'show logs', 'clear logs', 'clear fileident', '?']

    def __init__(self, open_port, host):
        self.open_port = open_port
        self.host = host

    def change_port(self, port):
        self.open_port = port

    @staticmethod
    def log(code):
        with open(Server.logfile, 'a', encoding='utf-8') as file:
            if type(code) == int:
                file.write(Server.log_text[code] + '\t' +
                           str(datetime.datetime.now())+'\n')
            else:
                file.write(code+'\t'+str(datetime.datetime.now())+'\n')

    @staticmethod
    def vernam_enc_dec(k, m):
        k = k*(len(m)//len(k)) + k[-(len(m) % len(k)):]
        return ''.join(map(chr, [i ^ x for i, x in zip(map(ord, m), map(ord, k))]))

    @staticmethod
    def start_program():
        User.create_file()
        while True:
            user_port = getpass.getpass(
                prompt="Enter port you want to use: ", stream=None)
            try:
                user_port = int(
                    user_port) if user_port != '' else Server.Def_PORT
                user_port = user_port if 1 < user_port < 65537 else Server.Def_PORT
                break
            except:
                continue
        a = Server(user_port, Server.Def_HOST)
        a.run()

    @staticmethod
    def listening(sock):
        while True:
            if Server.listen_flag:
                try:
                    conn, addr = sock.accept()
                except:
                    break
                thread = ClientThread(len(Server.threadlist), conn, addr)
                Server.threadlist.append(thread)
                thread.start()
            else:
                continue

    def run(self):
        Server.log(1)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            while True:
                try:
                    s.bind((self.host, self.open_port))
                    break
                except:
                    self.change_port(self.open_port+1)
                    Server.log(7)
            s.listen(5)
            thread = threading.Thread(
                target=Server.listening, args=(s,))
            Server.threadlist.append(thread)
            thread.start()
            Server.log(2)
            print(f'listen {self.open_port}')
            while True:
                command = input('enter the command (? for commands list): ')
                if command == 'off':
                    Server.log(6)
                    for n, c in Server.usernames:
                        c.close()
                    raise SystemExit
                elif command == '?':
                    print(', '.join(Server.commands))
                elif command == 'listen':
                    Server.listen_flag = True
                    Server.log(2)
                    print(f'listen {self.open_port}')
                elif command == 'pause':
                    Server.listen_flag = False
                    Server.log(10)
                    print(f'pause {self.open_port}')
                elif command == 'clear fileident':
                    Server.log(12)
                    with open(User.for_users, 'w', encoding='utf-8') as ss:
                        pass
                elif command == 'clear logs':
                    print('clear logs...')
                    with open(Server.logfile, 'w', encoding='utf-8') as ss:
                        pass
                elif command == 'show logs':
                    Server.log(11)
                    with open(Server.logfile, 'r', encoding='utf-8') as ss:
                        text = ss.read()
                        print(text)


class User():
    for_users = 'saved_users.csv'
    userlist = []

    @staticmethod
    def create_file():
        if User.for_users in os.listdir(os.getcwd()):
            with open(User.for_users, encoding='utf-8') as s:
                reader = csv.reader(s, delimiter=';')
                User.userlist = [row for row in reader]
        else:
            a = open(User.for_users, 'w', encoding='utf-8')
            a.close()

    @staticmethod
    def sync():
        with open(User.for_users, 'w', encoding='utf-8') as s:
            writer = csv.writer(s, delimiter=';')
            writer.writerows(User.userlist)

    @staticmethod
    def token():
        from random import randint
        return ''.join([chr(randint(1, 2000)) for i in range(40)])


class ClientThread(threading.Thread):
    def __init__(self, name, connector, addr):
        threading.Thread.__init__(self)
        self.name = name
        self.connector = connector
        self.clientaddr = addr

    def run(self):
        name = ClientThread.ident(self.connector)
        Server.usernames.append((name, self.connector))
        Server.log('identification')
        self.message_hist()
        Server.log('message history was sent')
        while True:
            text = ClientThread.recv_(self.connector)
            if not text:
                break
            ClientThread.send_(text, name)

    @staticmethod
    def new_user(sock):
        sock.send('name'.encode())
        name = sock.recv(1024).decode()
        sock.send(f'password,{name}'.encode())
        answer = sock.recv(1024).decode()
        password = Server.vernam_enc_dec(
            Server.key, answer)
        token = User.token()
        sock.send(f'Hello,{name},{token}'.encode())
        User.userlist.append([name, password, token])
        User.sync()
        return name

    @ staticmethod
    def ident(sock):
        if len(User.userlist) == 0:
            return ClientThread.new_user(sock)
        else:
            sock.send('token'.encode())
            token = sock.recv(1024).decode()
            for row in User.userlist:
                if row[2] == token:
                    sock.send(f'Hello,{row[0]}'.encode())
                    return row[0]
            else:
                sock.send('name'.encode())
                name = sock.recv(1024).decode()
                for i, row in enumerate(User.userlist):
                    if row[0] == name:
                        while True:
                            sock.send(f'password,{name}'.encode())
                            passwd = sock.recv(1024).decode()
                            data = Server.vernam_enc_dec(
                                Server.key, passwd)
                            if data == row[1]:
                                token = User.token()
                                sock.send(f'Hello,{row[0]},{token}'.encode())
                                User.userlist[i].pop()
                                User.userlist[i].append(token)
                                User.sync()
                                return row[0]
                else:
                    sock.send(f'password,{name}'.encode())
                    answer = sock.recv(1024).decode()
                    password = Server.vernam_enc_dec(
                        Server.key, answer)
                    token = User.token()
                    sock.send(f'Hello,{name},{token}'.encode())
                    User.userlist.append([name, password, token])
                    User.sync()
                    return name

    @staticmethod
    def send_(message, name):
        for name_, conn in Server.usernames:
            if name_ != name:
                conn.send(f'{name}:{message}'.encode())
        with open(Server.history, 'a', encoding='utf-8') as a:
            a.write(f'{name}:{message}\n')

    @staticmethod
    def recv_(conn):
        try:
            text = conn.recv(1024)
            return text.decode()
        except:
            pass

    def message_hist(self):
        if Server.history in os.listdir(os.getcwd()):
            with open(Server.history, 'r', encoding='utf-8') as ss:
                a = ss.read()
                if len(a) == 0:
                    self.connector.send('no messages'.encode())
                else:
                    self.connector.send(f'{a}'.encode())
        else:
            a = open(Server.history, 'w', encoding='utf-8')
            self.connector.send('no messages'.encode())
            a.close()


if __name__ == '__main__':
    Server.start_program()
