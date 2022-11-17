# coding: utf-8

import time
import socket
import selectors
import signal
import logging
import argparse
from sqlite3 import connect

# configure logger output format
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('Load Balancer')


# used to stop the infinity loop
done = False

sel = selectors.DefaultSelector()

policy = None
mapper = None


# implements a graceful shutdown
def graceful_shutdown(signalNumber, frame):  
    logger.debug('Graceful Shutdown...')
    global done
    done = True


# n to 1 policy
class N2One:
    def __init__(self, servers):
        self.servers = servers  

    def select_server(self):
        return self.servers[0]

    def update(self, *arg):
        pass


# round robin policy
class RoundRobin:
    def __init__(self, servers):
        self.servers = servers
        self.serverIndex = -1

    def select_server(self):
        self.serverIndex += 1
        return self.servers[(self.serverIndex) % len(self.servers)]
        
    def update(self, *arg):
        pass


# least connections policy
class LeastConnections:
    def __init__(self, servers):
        self.servers = servers
        self.connections = {}               # dic -> { server : int }
        for server in self.servers:
            self.connections[server] = 0

    def select_server(self):
        selectedServer = self.servers[0]
        for server in self.servers:
            if (self.connections[server] < self.connections[selectedServer]):
                selectedServer = server
        self.connections[selectedServer] += 1    
        return selectedServer 

    def update(self, *arg):
        if arg[0] in self.connections.keys():
            self.connections[arg[0]] -= 1

# least response time
class LeastResponseTime:
    def __init__(self, servers):
        self.servers = servers
        self.ctr = 0
        self.connections = {}               # dic -> { server : int }
        for server in self.servers:
            self.connections[server] = 0     
        self.averageServerSpeed = {}       # dic = { server : [ sum_times, count, average ] }
        for server in self.servers:
            self.averageServerSpeed[server] = [0, 0, 0]
        self.currentConnections = []       # [ (server, init_time) ] 
 
    def select_server(self):
        ctr = min(self.averageServerSpeed, key = self.averageServerSpeed.__getitem__)
        if ctr == 0: 
            selectedServer = self.servers[self.ctr]
            self.ctr += 1
            if self.ctr == 4:
                self.ctr = 0   
        else:
            selectedServer = self.servers[0]
            for server in self.servers:
                if (self.averageServerSpeed[server][2] <= self.averageServerSpeed[selectedServer][2]) and self.averageServerSpeed[server][1] < self.averageServerSpeed[selectedServer][1]:
                    selectedServer = server
                elif (self.averageServerSpeed[server][2] < self.averageServerSpeed[selectedServer][2]) and self.averageServerSpeed[server][1] == self.averageServerSpeed[selectedServer][1]:
                    selectedServer = server
        self.averageServerSpeed[selectedServer][1] += 1
        self.currentConnections.append([selectedServer, time.time()])
        return selectedServer 

    def update(self, *arg): 
        total_time = time.time()
        server = arg[0]
        for connection in self.currentConnections:
            if connection[0] == server:
                total_time -= connection[1]
                self.currentConnections.remove(connection)
                break
        if total_time != -1:
            self.averageServerSpeed[server][0] += total_time
            self.averageServerSpeed[server][2] = self.averageServerSpeed[server][0] / self.averageServerSpeed[server][1]


POLICIES = {
    "N2One": N2One,
    "RoundRobin": RoundRobin,
    "LeastConnections": LeastConnections,
    "LeastResponseTime": LeastResponseTime
}

class SocketMapper:
    def __init__(self, policy):
        self.policy = policy
        self.map = {}

    def add(self, client_sock, upstream_server):
        client_sock.setblocking(False)
        sel.register(client_sock, selectors.EVENT_READ, read)
        upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream_sock.connect(upstream_server)
        upstream_sock.setblocking(False)
        sel.register(upstream_sock, selectors.EVENT_READ, read)
        logger.debug("Proxying to %s %s", *upstream_server)
        self.map[client_sock] =  upstream_sock

        
    def delete(self, sock):
        
        sel.unregister(sock)
        sock.close()
        if sock in self.map:
            self.map.pop(sock)

    def get_sock(self, sock):
        for client, upstream in self.map.items():
            if upstream == sock:
                return client
            if client == sock:
                return upstream
        return None
    
    def get_upstream_sock(self, sock):
        return self.map.get(sock)

    def get_all_socks(self):
        """ Flatten all sockets into a list"""
        return list(sum(self.map.items(), ())) 

def accept(sock, mask):
    client, addr = sock.accept()
    logger.debug("Accepted connection %s %s", *addr)
    mapper.add(client, policy.select_server())

def read(conn,mask):
    data = conn.recv(4096)
    if len(data) == 0: # No messages in socket, we can close down the socket
        mapper.delete(conn)
    else:
        mapper.get_sock(conn).send(data)


def main(addr, servers, policy_class):
    global policy
    global mapper

    # register handler for interruption 
    # it stops the infinite loop gracefully
    signal.signal(signal.SIGINT, graceful_shutdown)

    policy = policy_class(servers)
    mapper = SocketMapper(policy)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(addr)
    sock.listen()
    sock.setblocking(False)

    sel.register(sock, selectors.EVENT_READ, accept)

    try:
        logger.debug("Listening on %s %s", *addr)
        while not done:
            events = sel.select(timeout=1)
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
                
    except Exception as err:
        logger.error(err)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pi HTTP server')
    parser.add_argument('-a', dest='policy', choices=POLICIES)
    parser.add_argument('-p', dest='port', type=int, help='load balancer port', default=8080)
    parser.add_argument('-s', dest='servers', nargs='+', type=int, help='list of servers ports')
    args = parser.parse_args()
    
    servers = [('localhost', p) for p in args.servers]
    
    main(('127.0.0.1', args.port), servers, POLICIES[args.policy])
