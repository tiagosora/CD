"""Middleware to communicate with PubSub Message Broker."""
import socket

from enum import Enum
from src.protocolo import MBProto
from collections.abc import Callable

class MiddlewareType(Enum):
    """Middleware Type."""
    CONSUMER = 1
    PRODUCER = 2

class Queue:
    """Representation of Queue interface for both Consumers and Producers."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        self.topic = topic
        self.type = _type
        
        self._host = "localhost"
        self._port = 5000
        self.mid_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mid_sock.connect((self._host, self._port))

        msg = MBProto.ack(str(self.__class__.__name__))
        MBProto.send_json(self.mid_sock, msg)

        self.mid_sock.setblocking(True)
        
    def push(self, value):
        """Sends data to broker."""
        return MBProto.publish(self.topic, value)

    def pull(self):
        """Receives (topic, data) from broker."""
        data = MBProto.recv_msg(self.mid_sock)
        if data:
            return data

    def list_topics(self, callback: Callable):
        """Lists all topics available in the broker."""
        self.callback = callback
        return MBProto.list()

    def cancel(self):
        """Cancel subscription."""
        return MBProto.unsubscribe(self.topic)

class JSONQueue(Queue):
    """Queue implementation with JSON based serialization."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        super().__init__(topic, _type)
        if _type == MiddlewareType.CONSUMER:
            msg = MBProto.subscribe(self.topic)
            MBProto.send_json(self.mid_sock, msg)

    def push(self, value):
        """Sends data to broker. """
        msg = super().push(value)
        MBProto.send_json(self.mid_sock, msg)

    def pull(self):
        """Receives (topic, data) from broker."""
        try:
            data = super().pull()
            msg = MBProto.recv_json(data)
            if msg.command == "publish":
                return msg.topic, msg.message
            elif msg.command == "list":
                self.callback(msg.topicList)
                self.pull()
        except:
            return None,None

    def list_topics(self, callback: Callable):
        """Lists all topics available in the broker."""
        msg = super().list_topics(callback)
        MBProto.send_json(self.mid_sock, msg)
    
    def cancel(self):
        """Cancel subscription."""
        msg = super().cancel()
        MBProto.send_json(self.mid_sock, msg)
    
class XMLQueue(Queue):
    """Queue implementation with XML based serialization."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        super().__init__(topic, _type)
        if _type == MiddlewareType.CONSUMER:
            msg = MBProto.subscribe(self.topic)
            MBProto.send_xml(self.mid_sock, msg)

    def push(self, value):
        """Sends data to broker. """
        msg = super().push(value)
        MBProto.send_xml(self.mid_sock, msg)

    def pull(self):
        """Receives (topic, data) from broker."""
        try:
            data = super().pull()
            msg = MBProto.recv_xml(data)
            if msg.command == "publish":
                return msg.topic, msg.message
            elif msg.command == "list":
                return self.callback(msg.topicList)
        except:
            return None,None

    def list_topics(self, callback: Callable):
        """Lists all topics available in the broker."""
        msg = super().list_topics(callback)
        MBProto.send_xml(self.mid_sock, msg)
    
    def cancel(self):
        """Cancel subscription."""
        msg = super().cancel()
        MBProto.send_xml(self.mid_sock, msg)

class PickleQueue(Queue):
    """Queue implementation with Pickle based serialization."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""
        super().__init__(topic, _type)
        if _type == MiddlewareType.CONSUMER:
            msg = MBProto.subscribe(self.topic)
            MBProto.send_pickle(self.mid_sock, msg)
        
    def push(self, value):
        """Sends data to broker. """
        msg = super().push(value)
        MBProto.send_pickle(self.mid_sock, msg)

    def pull(self):
        """Receives (topic, data) from broker."""
        try:
            data = super().pull()
            msg = MBProto.recv_pickle(data)
            if msg.command == "publish":
                return msg.topic, msg.message
            elif msg.command == "list":
                self.callback(msg.topicList)
                self.pull()
        except:
            return None,None

    def list_topics(self, callback: Callable):
        """Lists all topics available in the broker."""
        msg = super().list_topics(callback)
        MBProto.send_pickle(self.mid_sock, msg)

    
    def cancel(self):
        """Cancel subscription."""
        msg = super().cancel()
        MBProto.send_pickle(self.mid_sock, msg)