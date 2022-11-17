import fcntl
import os
import selectors
import socket
import sys
from PIL import Image

from src.protocolo import IMGProto

class Client:
    """
        list : Listar todas as imagens em sistema
        get <identifier> : Obter imagem a partir do identificador 
    """

    def __init__(self, port):
        """Initializes chat client."""
        self.host = 'localhost'
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.host, self.port))
        except:
            sys.exit("\nERROR: Daemon already in use! Please reconnect using a diferent address port.\n")

        self.all_pics = {}

        print("\nAvailable actions:\n" +
        "   list : Listar todas as imagens em sistema\n" +
        "   get <identifier> : Obter imagem a partir do identificador\n")

        self.sel = selectors.DefaultSelector()
        self.sel.register(self.socket, selectors.EVENT_READ, self.read)

    def read(self, conn, mask):
        msg = IMGProto.recv_msg(conn)
        print("New command -> ",msg.command)
        if msg.command == 'imgList':
            self.all_pics = msg.imgList
            for imagehash in self.all_pics.keys():
                print("[",imagehash,", ",self.all_pics[imagehash][0],", ",self.all_pics[imagehash][1],"]")
        elif msg.command == 'searchResponse':
            try:
                im = Image.open(msg.img)
                im.show()   
            except:
                fileA = open('recebido.jpg', 'wb')
                im = msg.img
                while im:
                    fileA.write(im)
                    im = self.socket.recv(2048)
                fileA.close()
                print("Imagem Received Sucessfully")
                imagem = Image.open("recebedido.jpg").frombytes()
                imagem.show()


    def get_data(self, stdin, mask):
        user_input = stdin.read().strip()       
        if user_input == 'list':
            list_message = IMGProto.imgList()
            IMGProto.send_msg(self.socket, list_message)
        elif user_input[0:4] == 'get ':
            imagehash = user_input[4:]
            msg = IMGProto.search(imagehash)
            IMGProto.send_msg(self.socket, msg)            
    
    def loop(self):
        """Loop indefinetely."""

        # Comandos que impedem o cliente de bloquear
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

        self.sel.register(sys.stdin, selectors.EVENT_READ, self.get_data)

        while True:
            sys.stdout.write('> ')
            sys.stdout.flush()
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)


    