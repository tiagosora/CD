import os
from random import randint
import selectors
from PIL import Image
from time import sleep
import imagehash
import socket
import glob

from scipy import rand
from src.protocolo import IMGProto

class Daemon:
    def __init__(self, folder, port):
        self.all_pics = {}          # dic { imghash : (size, port) }
        self.self_pics = {}         # dic { imghash : (size, path) }
        self.my_connections = {}    # { port: socket_to_port }
        self.folder = folder
        self.my_client = None

        self.hash_images()

        print("My folder: ", self.folder)
        self.my_port = port
        self.first_port = 5000

        # BIND SOCKET
        self.sel = selectors.DefaultSelector()
        self.bindSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bindSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bindSocket.bind(('localhost', self.my_port))
        self.bindSocket.listen(100)
        self.sel.register(self.bindSocket, selectors.EVENT_READ, self.accept)

        # FIRST CONNECTION SOCKET (5000)
        self.connSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            if (self.my_port != self.first_port):
                self.connSocket.connect(('localhost', self.first_port))
                self.my_connections[self.first_port] = self.connSocket
                msg = IMGProto.ackDaemons(self.my_port)
                IMGProto.send_msg(self.connSocket, msg)
            else:
                for imghash in self.self_pics.keys():
                    self.all_pics[imghash]= (self.self_pics[imghash][0], self.my_port)
                print("I might be the first!")
                print("Number of Pics in self_pics ",len(self.self_pics))
        except: raise
        
        self.sel.register(self.connSocket, selectors.EVENT_READ, self.read)

        # CLIENT SOCKET
        self.client_port = randint(8000, 8501)
        print("Port para o Cliente: ", self.client_port)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.bind(('localhost', self.client_port))
        self.client_socket.listen(0)
        self.sel.register(self.client_socket, selectors.EVENT_READ, self.acceptClient)

    def accept(self, sock: socket.socket, mask):
        conn, addr = sock.accept()
        print("socket: ", conn, "addr: ", addr)
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self.read)

    def acceptClient(self, sock: socket.socket, mask):
        conn, addr = sock.accept()
        self.my_client = conn
        print("socket: ", conn, "addr: ", addr)
        conn.setblocking(False)
        self.sel.unregister(self.client_socket)
        self.client_socket.close()
        self.sel.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):
        try: 
            data = IMGProto.recv_msg(conn)
            if data:
                try:
                    if data.command == "imgList":
                        msg = IMGProto.imgList(self.all_pics)
                        IMGProto.send_msg(self.my_client, msg)

                    elif data.command == "search":
                        id = data.imgID
                        self.searchImage(id)

                    elif data.command == 'ackDaemons':
                        newSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        newSocket.connect(('localhost', data.port))
                        print("Connected to ('localhost', ", data.port,")")
                        self.my_connections[data.port] = newSocket
                        
                        # Notificar quais os daemons já ligados
                        msg = IMGProto.deamonListMsg(list(self.my_connections.keys()))
                        IMGProto.send_msg(newSocket, msg)

                        # Pedir uma atualização das imagens
                        self.sendAllImages(newSocket)
                    
                    elif data.command == 'askConnect':
                        newSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        newSocket.connect(('localhost', data.port))
                        print("Connected to ('localhost', ", data.port,")")
                        self.my_connections[data.port] = newSocket
                        
                    elif data.command == "listDaemon":
                        newPortsList = data.daemonList
                        myPortsList = self.my_connections.keys()
                        for port in newPortsList:
                            if (port not in myPortsList and port != self.my_port):
                                newSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                newSocket.connect(('localhost', port))
                                print("Connected to ('localhost', ", port,")")
                                self.my_connections[port] = newSocket
                                msg = IMGProto.askConnect(self.my_port)
                                IMGProto.send_msg(newSocket, msg)

                    elif data.command == 'updateImg':
                        self.all_pics = data.imgList
                        if (self.updateAllPics()):
                            print(list(self.my_connections.keys()))
                            for port in self.my_connections.keys():
                                msg = IMGProto.updateImgResMsg(self.all_pics)
                                IMGProto.send_msg(self.my_connections[port], msg)

                    elif data.command == 'updateImgRes':
                        self.all_pics = data.imgList
                        print("ImageHash List Updated. Number of items: ",len(self.all_pics))
                        self.updateSelfPics()

                    elif data.command == 'searchDaemon':
                        self.sendImage(data.imgID, data.port)

                    elif data.command == 'searchDaemonResponse':
                        msg = IMGProto.searchResponse(data.img)
                        IMGProto.send_msg(self.my_client, msg)

                except:
                    raise 
            else: pass
        except ConnectionError:
            print("ConnectionError")

    def hash_images(self):        
        for filename in glob.glob(self.folder + '/*.jpg'): 
            im = Image.open(filename)
            im_hash = imagehash.average_hash(im)
            im_size = im.width * im.height
            if im_hash in self.self_pics.keys() and self.self_pics[im_hash][0] < im_size:
                os.remove(filename)    
            self.self_pics[im_hash] = (im_size, filename)

    def updateAllPics(self):
        response = False
        for selfImageHash in self.self_pics.keys():
            if selfImageHash not in self.all_pics.keys():
                self.all_pics[selfImageHash] = (self.self_pics[selfImageHash][0], self.my_port)
                response = True
            elif self.all_pics[selfImageHash][1] < self.self_pics[selfImageHash][0]:
                self.all_pics[selfImageHash] = (self.self_pics[selfImageHash][0], self.my_port)
                response = True
            else:
                self.self_pics.pop(selfImageHash)
        return response

    def updateSelfPics(self):
        for imagehashS in self.self_pics.keys():
            if imagehashS in self.all_pics.keys() and self.all_pics[imagehashS][1] != self.my_port:
                # Search that imagehash in its folder and delete it
                for filename in glob.glob(self.folder + '/*.jpg'): 
                    im = Image.open(filename)
                    im_hash = imagehash.average_hash(im)
                    if im_hash == imagehashS:
                        print("Removed duplicated image from my file: ",filename)
                        os.remove(filename)

    def sendAllImages(self, conn: socket):
        msg = IMGProto.updateImgMsg(self.all_pics)
        IMGProto.send_msg(conn, msg)

    def searchImage(self, id):
        for img in self.all_pics.keys():
            if img.__str__() == id:
                if self.all_pics[img][1] == self.my_port:
                    im_path = self.self_pics[img][1]
                    msg = IMGProto.searchResponse(im_path)
                    IMGProto.send_msg(self.my_client, msg)
                else:
                    port = self.all_pics[img][1]
                    conn = self.my_connections[port]
                    msg = IMGProto.searchDaemon(id, self.my_port)
                    IMGProto.send_msg(conn, msg)
                return
        print("Image not found using this identifier!")

    def sendImage(self, img, port):
        pedinte = self.my_connections[port]
        im_path = self.self_pics[imagehash.hex_to_hash(img)][1]
        fileA = open(im_path, 'rb')
        im_data = fileA.read(2048)
        while im_data:
            msg = IMGProto.searchDaemonRes(im_data)
            IMGProto.send_msg(pedinte, msg)
            im_data = fileA.read(2048)
        fileA.close()
            
    
    def loop(self):
        """Loop indefinetely."""
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)