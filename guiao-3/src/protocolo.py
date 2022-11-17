"""Protocol for Message Broker"""
import xml.etree.cElementTree as C
import pickle
import json

from socket import socket

class Message:
    """Message Type."""

    def __init__(self, command):
        self.command = command

    def __repr__(self) -> str:
        return f'"command": "{self.command}"'

    def dic(self):
        return {"command":self.command}

    def getcommand(self):
        return self.command

class AckMessage(Message):
    """Message to identify serializer."""

    def __init__(self, command, serializer):
        super().__init__(command)
        self.serializer = serializer

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}, "serializer": "{self.serializer}"}}'

    def dic(self):
        return {"command":super().getcommand() , "serializer":self.serializer}

class SubscribeMessage(Message):
    """Message to subscribe a topic."""

    def __init__(self, command, topic):
        super().__init__(command)
        self.topic = topic

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}, "topic": "{self.topic}"}}'

    def dic(self):
        return {"command":self.getcommand(), "topic":self.topic}

class UnsubscribeMessage(Message):
    """Message to unsubscribe a topic."""

    def __init__(self, command, topic):
        super().__init__(command)
        self.topic = topic

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}, "topic": "{self.topic}"}}'
    
    def dic(self):
        return {"command":super().getcommand(), "topic":self.topic}

class PublishMessage(Message):
    """Message published in a topic."""

    def __init__(self, command, topic, message):
        super().__init__(command)
        self.message = message
        self.topic = topic

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}, "topic": "{self.topic}", "message": "{self.message}"}}'

    def dic(self):
        return {"command":super().getcommand(), "topic":self.topic, "message":self.message}

class ListMessage(Message):
    """Message to list existing topics"""

    def __init__(self, command):
        super().__init__(command)

    def __repr__(self) -> str:
        return super().__repr__()

    def dic(self):
        return {"command":super().getcommand()}

class ListResponse(Message):
    """Message to return existing topics"""

    def __init__(self, command, topicList):
        super().__init__(command)
        self.topicList = topicList

    def __repr__(self) -> str:
        return f'{{{super().__repr__()}, "topicList": "{self.topicList}"}}'

    def dic(self):
        return {"command":super().getcommand(), "topicList":self.topicList}

class MBProto:
    """Message Broker Protocol."""

    @classmethod
    def ack(cls, serializer: str) -> AckMessage:
        """Creates a AckMessage object."""
        return AckMessage("ack", serializer)

    @classmethod
    def subscribe(cls, topic) -> SubscribeMessage:
        """Creates a SubscribeMessage object."""
        return SubscribeMessage("subscribe", topic)

    @classmethod
    def publish(cls, topic, message) -> PublishMessage:
        """Creates a PublishMessage object."""
        return PublishMessage("publish", topic, message)

    @classmethod
    def list(cls, topicList = None) -> ListMessage or ListResponse:
        """Creates a ListMessage object."""
        if topicList:
            return ListResponse("list", topicList)
        return ListMessage("list")

    @classmethod
    def unsubscribe(cls, topic) -> UnsubscribeMessage:
        """Creates a UnsubscribeMessage object."""
        return UnsubscribeMessage("unsubscribe", topic)

    @classmethod
    def send_msg(cls, connection: socket, msg: bytes):
        """Sends a Message object."""
        header = len(msg).to_bytes(2, 'big')
        try:
            connection.send(header + msg)
        except: pass

    @classmethod
    def send_json(cls, connection: socket, msg: Message):
        """Sends the encoded message."""
        json_msg = json.dumps(msg.dic()).encode("UTF-8")
        cls.send_msg(connection, json_msg)
    
    @classmethod
    def send_xml(cls, connection: socket, msg: Message):
        """Sends a Message object."""
        dic = msg.dic()
        for element in dic.keys():
            dic[element] = str(dic[element])
        elem = C.Element("msg", dic)
        encoded_msg = C.tostring(elem)
        cls.send_msg(connection, encoded_msg)

    @classmethod
    def send_pickle(cls, connection: socket, msg: Message):
        """Sends a Message object."""
        pickle_msg = pickle.dumps(msg.dic())
        cls.send_msg(connection, pickle_msg)

    @classmethod
    def msg_type(cls, msg) -> Message:
        command = msg["command"]

        if command == "subscribe":
            topic = msg["topic"]
            return cls.subscribe(topic)
        elif command == "publish":
            message = msg["message"]
            topic = msg["topic"]
            return cls.publish(topic, message)
        elif command == "list":
            if msg["topicList"]:
                topicList = msg["topicList"]
                return cls.list(topicList)
            return cls.list()
        elif command == "unsubscribe":
            topic = msg["topic"]
            return cls.unsubscribe(topic)

    @classmethod
    def recv_msg(cls, connection: socket):
        """Receives through a connection a Message object."""
        try:
            headerBytes = connection.recv(2)
            header = int.from_bytes(headerBytes,'big')
            return connection.recv(header)
        except:
            raise MBProtoBadFormat()

    @classmethod
    def recv_json(cls, data: bytes):
        msg = json.loads(data.decode('UTF-8'))
        return cls.msg_type(msg)

    @classmethod 
    def recv_xml(cls, data: bytes):
        my_xml = C.fromstring(data.decode('utf-8'))
        loaded_msg = my_xml.attrib

        return cls.msg_type(loaded_msg)

    @classmethod
    def recv_pickle(cls, data: bytes):
        msg = pickle.loads(data)
        return cls.msg_type(msg)

class MBProtoBadFormat(Exception):
    """Exception when source message is not MBProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8") 