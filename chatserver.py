import socket
import select

MAX_QUEUED_CONNECTIONS = 5
TIMEOUT = 1 # 1 second
BUFFER_LENGTH = 1024

class ChatServer:
    def __init__(self):
        self.socket = None 
        self.connected_clients = []
    
    def start(self, address, port):
        """initialize the server socket using the specified address and port"""
        
        # create a socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # bind a socket        
        self.socket.bind((address, port))
        
        # listen to connections        
        self.socket.listen(MAX_QUEUED_CONNECTIONS)
        
    def run(self):
        """main loop"""
        while True:
            self.check_new_connections()
            if self.connected_clients:
                self.check_new_messages()
                
        # clean up
        self.socket.close()            
                
            
    def check_new_connections(self):
        """check for new client connections"""
        queued_connections = select.select([self.socket], [], [], TIMEOUT)[0] 
    
        # accept new connections
        for connection in queued_connections:
            print("new connection")
            # accept the new connection
            client_socket = connection.accept()[0]
                        
            # add it to the client sockets list
            self.connected_clients.append(client_socket)     
        
    def check_new_messages(self):
        """check for new messages from the connected clients, handles disconnections too"""        
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
                    self.remove_client(client_socket)
            except ConnectionResetError:
                print("connection reset for socket {}".format(client_socket))
                self.close_client(client_socket)
                
    def remove_client(self, client_socket):
        """shutdown the socket then close it"""
        client_socket.shutdown(socket.SHUT_WR)  
        self.close_client(client_socket)
                
    def close_client(self, client_socket):
        """close the socket and remove it from the list of connected clients"""
        client_socket.close()
        self.connected_clients.remove(client_socket)  
     

# main code
chat_server= ChatServer()

chat_server.start('', 5555)

chat_server.run()

