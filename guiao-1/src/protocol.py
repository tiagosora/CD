"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from socket import socket
from datetime import datetime
class Message:
    """Message Type."""
    def __init__(self, var = None):
        self.var = var
class JoinMessage(Message):
    """Message to join a chat channel."""
    def __init__(self,ch = None, var = "join"):
        super().__init__(var)
        self.var = var
        self.ch = ch
    def __str__(self):
        dic = {
            "command" : self.var,
            "channel" : self.ch
        }
        return json.dumps(dic)
class RegisterMessage(Message):
    """Message to register username in the server."""
    def __init__(self, user = None, var = "register"):
        super().__init__(var)
        self.var = var 
        self.user = user
    def __str__(self):
        dic = {
            "command" : self.var,
            "user" : self.user
        }
        return json.dumps(dic)
class TextMessage(Message):
    """Message to chat with other clients."""
    def __init__(self, m = None, ch = None, var = "message"):       
        super().__init__(var)
        self.var = var
        self.m = m
        self.ch = ch
    def __str__(self):
        if(self.ch != None):
            dic = { "command" : self.var,
                    "message" : self.m,
                    "ts" : int(datetime.now().timestamp()),
                    "channel" : self.ch }
        else:
            dic = { "command" : self.var,
                    "message" : self.m,
                    "ts" : int(datetime.now().timestamp()) }
        return json.dumps(dic)
class CDProto:
    """Computação Distribuida Protocol."""
    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        return RegisterMessage(username)
    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        return JoinMessage(channel)
    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
        return TextMessage(message, channel)
    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        jsonmsg = bytes(msg.__str__(),encoding="utf-8")
        if(len(jsonmsg)>pow(2,16)):
            raise CDProtoBadFormat(jsonmsg)
        connection.sendall(len(jsonmsg).to_bytes(2,'big')+jsonmsg) 
    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        msg = connection.recv(int.from_bytes(connection.recv(2),'big'))
        jsonmsg = msg.decode("utf-8")
        if(jsonmsg != ""):
            try:
                jsonLoad = json.loads(jsonmsg)
            except json.decoder.JSONDecodeError:
                raise CDProtoBadFormat(jsonmsg)
            if(jsonLoad["command"] == "register"):
                return CDProto.register(jsonLoad["user"])
            elif(jsonLoad["command"] == "join"):
                return CDProto.join(jsonLoad["channel"])
            elif(jsonLoad["command"] == "message"):
                if("channel" in jsonLoad):
                    return CDProto.message(jsonLoad["message"],jsonLoad["channel"])
                else:
                    return CDProto.message(jsonLoad["message"])
class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""
    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg
    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
