"""CD Chat client program"""
import fcntl
import logging
import os
import selectors
import socket
import sys
from .protocol import CDProto
logging.basicConfig(filename=f"{sys.argv[0]}.log", level=logging.DEBUG)
orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)
class Client:
    """Chat Client process."""
    def __init__(self, name: str = "Alberto"):
        """Initializes chat client."""
        self.name = name
        self.Csock = socket.socket()
        self.Csel = selectors.DefaultSelector()
        self.ch = None
    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.Csock.connect(('localhost',1234))
        self.Csel.register(sys.stdin, selectors.EVENT_READ, self.got_keyboard_data)
        self.Csel.register(self.Csock, selectors.EVENT_READ, self.read)
        CDProto.send_msg(self.Csock,CDProto.register(self.name))
        print("New conection to the Server!")
    def read(self, conn , mask):
        data = CDProto.recv_msg(self.Csock)
        if (type(data) != None and data != None):
            print(data.m)
            logging.debug(data.m)
    def got_keyboard_data(self, stdin , mask):
        input = sys.stdin.read().rstrip()   
        if(input == "exit"):
            self.Csel.unregister(sys.stdin)
            self.Csel.unregister(self.Csock)
            self.Csock.close()
            sys.exit(0)
        elif(input.startswith("/join ")):
            msg = CDProto.join(input[6:])
            self.ch = input[6:]
            CDProto.send_msg(self.Csock, msg)
        else:
            mensagem = CDProto.message(input)
            CDProto.send_msg(self.Csock,mensagem)
            print(f"< {mensagem.m}")   
            logging.debug(mensagem.m)
    def loop(self):
        """Loop indefinetely."""
        sys.stdout.write("\r ->")
        sys.stdout.flush()
        while True:
            for key, mask in self.Csel.select():
                callback = key.data
                callback(key.fileobj, mask)