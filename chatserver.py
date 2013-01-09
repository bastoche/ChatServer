import socket
import select

MAX_QUEUED_CONNECTIONS = 5
TIMEOUT = 1 # 1 second
BUFFER_LENGTH = 1024

class ChatServer:
    def __init__(self):
        self.socket = None 
        self.connected_clients = []
        self.logged_clients = []
    
    def initialize(self, address, port):
        # create a socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # bind a socket        
        self.socket.bind((address, port))
        
        # listen to connections        
        self.socket.listen(MAX_QUEUED_CONNECTIONS)
        
    def run(self):
        # main loop
        while True:
            self.check_new_connections()
            if self.connected_clients:
                self.check_new_messages()
                
        # clean up
        self.socket.close()            
                
            
    def check_new_connections(self):
        # check for new connections
        queued_connections = select.select([self.socket], [], [], TIMEOUT)[0] 
    
        # accept new connections
        for connection in queued_connections:
            print("new connection")
            # accept the new connection
            client_socket = connection.accept()[0]
            # add it to the client sockets list
            self.connected_clients.append(client_socket)     
        
    def check_new_messages(self):
        client_sockets_to_read = select.select(self.connected_clients, [], [], TIMEOUT)[0]
        
        for client_socket in client_sockets_to_read:                
            try:
                message = client_socket.recv(BUFFER_LENGTH)
                print("received message {} with length {}".format(message, len(message)))            
                if message:
                    # broadcast message to all connected clients
                    for client_socket in self.connected_clients:
                        client_socket.send(message)
                else:                                                                
                    # close the socket
                    print("shutdown and close")
                    client_socket.shutdown(socket.SHUT_WR)                
                    client_socket.close()
                    self.connected_clients.remove(client_socket)
            except ConnectionResetError:
                print("connection reset for socket {}".format(client_socket))
                client_socket.close()
                self.connected_clients.remove(client_socket)                     


chat_server= ChatServer()

chat_server.initialize('', 5555)

chat_server.run()

