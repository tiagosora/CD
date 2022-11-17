"""Protocol"""

import pickle
from socket import socket

class Message:

    def __init__(self, command):
        self.command = command

    def __repr__(self) -> str:
        return f'"command": "{self.command}"'

    def dic(self):
        return {"command":self.command}

    def getcommand(self):
        return self.command

""" Mensagens Client <-> Daemon """

class AckMessage(Message):

    def __init__(self, command):
        super().__init__(command)

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}}}'

    def dic(self):
        return {"command":super().getcommand()}

class ImgListRequest(Message):
    
    def __init__(self, command):
        super().__init__(command)

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}}}'

    def dic(self):
        return {"command":super().getcommand()}

class ImgListResponse(Message):
    
    def __init__(self, command, imgList):
        super().__init__(command)
        self.imgList = imgList

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}, "imgList": "{self.imgList}"}}'

    def dic(self):
        return {"command":super().getcommand(), "imgList":self.imgList}

class ImgRequestMessage(Message):

    def __init__(self, command, imgID):
        super().__init__(command)
        self.imgID = imgID

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}, "imgID": "{self.imgID}"}}'

    def dic(self):
        return {"command":super().getcommand(), "imgID":self.imgID}

class ImgResponseMessage(Message):

    def __init__(self, command, img):
        super().__init__(command)
        self.img = img

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}, "img": "{self.img}"}}'

    def dic(self):
        return {"command":super().getcommand(), "img":self.img}

""" Mesagens Daemon <-> Daemon """

class AckDaemonsMessage(Message):
    
    def __init__(self, command, port):
        super().__init__(command)
        self.port = port

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}, "port": "{self.port}"}}'

    def dic(self):
        return {"command":super().getcommand(), "port":self.port}

class AskConnectMessage(Message):
    
    def __init__(self, command, port):
        super().__init__(command)
        self.port = port

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}, "port": "{self.port}"}}'

    def dic(self):
        return {"command":super().getcommand(), "port":self.port}

class ListDaemonMessage(Message):

    def __init__(self, command, daemonList):
        super().__init__(command)
        self.daemonList = daemonList

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}, "daemonList": "{self.daemonList}"}}'

    def dic(self):
        return {"command":super().getcommand(), "daemonList":self.daemonList}

class UpdateImgMessage(Message):
    
    def __init__(self, command, imgList):
        super().__init__(command)
        self.imgList = imgList

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}, "imgList": "{self.imgList}"}}'

    def dic(self):
        return {"command":super().getcommand(), "imgList":self.imgList}

class UpdateResMessage(Message):
    
    def __init__(self, command, imgList):
        super().__init__(command)
        self.imgList = imgList

    def __repr__(self):
        return f'{{{super().__repr__()}, "imgList": "{self.imgList}"}}'

    def dic(self):
        return {"command":super().getcommand(), "imgList":self.imgList}

class ImgRequestDaemon(Message):
    
    def __init__(self, command, imgID, port):
        super().__init__(command)
        self.imgID = imgID
        self.port = port

    def __repr__(self):
        return f'{{{super().__repr__()}, "imgID": "{self.imgID}", "port": "{self.port}"}}'

    def dic(self):
        return {"command":super().getcommand(), "imgID":self.imgID, "port":self.port}

class ImgResponseDaemon(Message):
    
    def __init__(self, command, img):
        super().__init__(command)
        self.img = img

    def __repr__(self):
        return f'{{{super().__repr__()}, "img": "{self.img}"}}'

    def dic(self):
        return {"command":super().getcommand(), "img":self.img}


class IMGProto:

    """ Métodos Client <-> Daemon """
    @classmethod
    def ack(cls) -> AckMessage:
        return AckMessage("ack")
    
    @classmethod 
    def imgList(cls, imgList = None) -> ImgListRequest or ImgListResponse:
        if imgList:
            return ImgListResponse("imgList", imgList)
        return ImgListRequest("imgList")

    @classmethod
    def search(cls, imageID) -> ImgRequestMessage:
        return ImgRequestMessage("search", imageID)

    @classmethod
    def searchResponse(cls, image) -> ImgResponseMessage:
        return ImgResponseMessage("searchResponse", image)

    """ Métodos Daemon <-> Daemon """
    @classmethod
    def ackDaemons(cls, port) -> AckDaemonsMessage:
        return AckDaemonsMessage("ackDaemons", port)
    
    @classmethod
    def askConnect(cls, port) -> AskConnectMessage:
        return AskConnectMessage("askConnect", port)

    @classmethod
    def deamonListMsg(cls, daemonList) -> ListDaemonMessage:
        return ListDaemonMessage("listDaemon", daemonList)

    @classmethod
    def updateImgMsg(cls, imgList) -> UpdateImgMessage:
        return UpdateImgMessage("updateImg", imgList)

    @classmethod
    def updateImgResMsg(cls, imgList) -> UpdateResMessage:
        return UpdateResMessage("updateImgRes", imgList)

    @classmethod
    def searchDaemon(cls, imageID, port) -> ImgRequestDaemon:
        return ImgRequestDaemon("searchDaemon", imageID, port)

    @classmethod
    def searchDaemonRes(cls, image) -> ImgResponseDaemon:
        return ImgResponseDaemon("searchDaemonResponse", image)    

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends a Message object."""
        msg = pickle.dumps(msg.dic())

        header = len(msg).to_bytes(2, 'big')
        try:
            connection.send(header + msg)
        except:
            print("Raising Error on Message Send")

    @classmethod
    def msg_type(cls, msg) -> Message:
        command = msg["command"]

        if command == "ack":
            return cls.ack()

        elif command == "imgList":
            try:
                imgList = msg["imgList"]
                return cls.imgList(imgList)
            except:
                return cls.imgList()

        elif command == "search":
            imageID = msg["imgID"]
            return cls.search(imageID)

        elif command == "searchResponse":
            image = msg["img"]
            return cls.searchResponse(image)
            
        ###################################

        elif command == "ackDaemons":
            port = msg["port"]
            return cls.ackDaemons(port)

        elif command == "askConnect":
            port = msg["port"]
            return cls.askConnect(port)        

        elif command == "listDaemon":
            daemonList = msg["daemonList"]
            return cls.deamonListMsg(daemonList)

        #################################

        elif command == "updateImg":
            imgList = msg["imgList"]
            return cls.updateImgMsg(imgList)

        elif command == "updateImgRes":
            imgList = msg["imgList"]
            return cls.updateImgResMsg(imgList)

        ###################################

        elif command == "searchDaemon":
            imageID = msg["imgID"]
            port = msg["port"]
            return cls.searchDaemon(imageID, port)

        elif command == "searchDaemonResponse":
            image = msg["img"]
            return cls.searchDaemonRes(image)
        

    @classmethod
    def recv_msg(cls, connection: socket):
        try:
            headerBytes = connection.recv(2)
            header = int.from_bytes(headerBytes,'big')
            data = connection.recv(header)
            msg = pickle.loads(data)
            return cls.msg_type(msg)
        except:
            pass

class IMGProtoBadFormat(Exception):

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8") 