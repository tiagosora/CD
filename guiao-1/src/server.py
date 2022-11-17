"""CD Chat server program."""
import logging
import socket
import selectors
from .protocol import CDProto
logging.basicConfig(filename="server.log", level=logging.DEBUG)
class Server:
    """Chat Server process."""
    def __init__(self):
        self.Ssock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.Ssock.bind(("localhost",1234))
        self.Ssock.listen(100)
        self.users = {}
        self.Csel = selectors.DefaultSelector()
        self.Csel.register(self.Ssock, selectors.EVENT_READ, self.accept)
    def accept(self, Ssock, mask):
        self.conn, self.address = self.Ssock.accept()
        self.users[self.conn] = []
        self.users[self.conn].append(None)
        print("New connection from ", self.address)
        self.Csel.register(self.conn, selectors.EVENT_READ, self.read)
    def read(self, Ssock, mask):
        try :
            self.recv = CDProto.recv_msg(Ssock)
            print('echoing', self.recv, 'to', self.conn)
            logging.debug(self.recv)
            if (type(self.recv) == None or self.recv == None):
                print('closing', Ssock)
                del self.users[Ssock]
                self.Csel.unregister(Ssock)
                self.conn.close()
            else:
                if(self.recv.var == "join"):
                    if(self.recv.ch in self.users[Ssock]):
                        self.users[Ssock].remove(self.recv.ch)
                    self.users[Ssock].append(self.recv.ch)
                if(self.recv.var == "message"):
                    channel = self.users[Ssock][len(self.users[Ssock])-1]
                    for client in self.users:
                        if(channel in self.users[client]):
                            CDProto.send_msg(client,self.recv)
                            logging.debug('sent "%s', self.recv)
        except ConnectionError:
            print('closing', Ssock)
            del self.users[Ssock]
            self.Csel.unregister(Ssock)
            self.conn.close()
    def loop(self):
        """Loop indefinetely."""
        while True:
            events = self.Csel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj,mask)