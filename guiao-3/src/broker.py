"""Message Broker"""
import enum
import selectors
import socket
import json

from typing import List
from src.protocolo import MBProto

class Serializer(enum.Enum):
    """Possible message serializers."""
    JSON = 0
    XML = 1
    PICKLE = 2

class Broker:
    """Implementation of a PubSub Message Broker."""

    def __init__(self):
        """Initialize broker."""
        self.canceled = False
        self._host = "localhost"
        self._port = 5000
        
        self.broker_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.broker_sock.bind((self._host, self._port))
        self.broker_sock.listen(100)
        
        self._selector = selectors.DefaultSelector()
        self._selector.register(self.broker_sock, selectors.EVENT_READ, self.accept)

        self.topics_list = set()                        # set dos tópicos disponíveis
        self.users_list = {}                            # user_socket (pub | sub) : serializer
        self.sub_topic_list = {}                        # topic : [(sub_address, sub_serializer)]
        self.topic_msg = {}                             # topic : last message

    def accept(self, sock: socket.socket, mask):        
        conn, addr = sock.accept()
        print("socket: ", conn, "addr: ", addr) 
        conn.setblocking(False)
        data = MBProto.recv_msg(conn)
        if data:
            data_final = json.loads(data)
            if data_final["serializer"] == "JSONQueue":
                self.users_list[conn] = Serializer.JSON
            elif data_final["serializer"] == "XMLQueue":
                self.users_list[conn] = Serializer.XML
            elif data_final["serializer"] == "PickleQueue":
                self.users_list[conn] = Serializer.PICKLE  
        self._selector.register(conn, selectors.EVENT_READ, self.read)

    def read(self, conn: socket.socket, mask):
        try:
            msg_init = MBProto.recv_msg(conn)
            if msg_init:
                try:
                    if self.users_list[conn] == Serializer.JSON:
                        msg = MBProto.recv_json(msg_init)
                    elif self.users_list[conn] == Serializer.XML:
                        msg = MBProto.recv_xml(msg_init)
                    elif self.users_list[conn] == Serializer.PICKLE:
                        msg = MBProto.recv_pickle(msg_init)

                    if msg.command == 'subscribe':
                        self.subscribe(msg.topic, conn, self.users_list[conn])
                    elif msg.command == 'unsubscribe':
                        self.unsubscribe(msg.topic, conn)
                    elif msg.command == 'publish':
                        self.put_topic(msg.topic, msg.message)
                        for topiclisted in self.sub_topic_list.keys():
                            if (msg.topic).startswith(topiclisted):
                                pub_msg = MBProto.publish(topiclisted, msg.message)
                                for sub in self.sub_topic_list[topiclisted]:
                                    if self.users_list[sub[0]] == Serializer.JSON:
                                        MBProto.send_json(sub[0], pub_msg)
                                    elif self.users_list[sub[0]] == Serializer.XML:
                                        MBProto.send_xml(sub[0], pub_msg)
                                    elif self.users_list[sub[0]] == Serializer.PICKLE:
                                        MBProto.send_pickle(sub[0], pub_msg)
                    elif msg.command == 'list':
                        list = self.list_topics()
                        msg = MBProto.list(list)
                        if self.users_list[conn] == Serializer.JSON:
                            MBProto.send_json(conn, msg)
                        elif self.users_list[conn] == Serializer.XML:
                            MBProto.send_xml(conn, msg)
                        elif self.users_list[conn] == Serializer.PICKLE:
                            MBProto.send_pickle(conn, msg)
                except:  pass

        except ConnectionError:
            print('closing', conn) 
            self.unsubscribe(msg.topic, conn)
            self._selector.unregister(conn)
            conn.close()   

    def list_topics(self) -> List[str]:
        """Returns a list of strings containing all topics containing values."""
        return list(self.topic_msg.keys())

    def get_topic(self, topic):
        """Returns the currently stored value in topic."""
        if topic in self.topics_list:
            return self.topic_msg[topic]
        return None

    def put_topic(self, topic, value):
        """Store in topic the value."""
        if topic in self.topic_msg.keys():
            self.topic_msg.update({topic: value})
        else:
            self.topic_msg[topic] = value
        self.topics_list.add(topic)
        print(f'\n>> The topic {topic} has a new message: {value}')

    def list_subscriptions(self, topic: str) -> List[socket.socket]:
        """Provide list of subscribers to a given topic."""
        if topic in self.sub_topic_list.keys():
            return self.sub_topic_list[topic]
        return None

    def subscribe(self, topic: str, address: socket.socket, _format: Serializer = None):
        """Subscribe to topic by client in address."""
        self.topics_list.add(topic)
        if address in self.users_list.keys():
            self.users_list.update({address: _format})
        else:
            self.users_list[address] = _format

        if topic in self.sub_topic_list.keys():
            self.sub_topic_list[topic].append((address, _format))
        else: 
            self.sub_topic_list[topic] = [(address, _format)] 

        for prevTopic in self.topics_list:
            if prevTopic in topic and prevTopic != topic:
                if prevTopic in self.sub_topic_list.keys():
                    for sub in self.sub_topic_list[prevTopic]:
                        self.sub_topic_list[topic].append(sub)
            if topic in prevTopic and prevTopic != topic:
                self.sub_topic_list[prevTopic].append((address, _format))

        print(f'\n>> {address} subscribed the topic {topic}')

        if topic in self.topic_msg.keys():
            last_msg = self.topic_msg[topic]
            if last_msg:
                msg = MBProto.publish(topic, last_msg)
                if _format == Serializer.JSON:
                    MBProto.send_json(address, msg)
                elif _format == Serializer.XML:
                    MBProto.send_xml(address, msg)
                elif _format == Serializer.PICKLE:
                    MBProto.send_pickle(address, msg)

    def unsubscribe(self, topic, address: socket.socket):
        """Unsubscribe to topic by client in address."""
        if (topic in self.sub_topic_list.keys()):
            format = self.users_list[address]
            self.sub_topic_list[topic].remove((address, format))

        print(f'\n>> {address} unsubscribed the topic {topic}')

    def run(self):
        """Run until canceled."""
        while not self.canceled:
            events = self._selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)