import socket
import select

# character encoding
ENCODING = "cp850"

# socket parameters
MAX_QUEUED_CONNECTIONS = 5
TIMEOUT = 1 # 1 second

# chat protocol
HEADER_LENGTH = 4
DELIMITER = '\n'

# chat commands 
LOGIN = "login"
LOGIN_REPLY = "login_reply"
BROADCAST = "broadcast"
WHISPER = "whisper"

LOG_ENABLED = True

class ChatServer:

    
    def __init__(self):
        self.socket = None 
        self.connected_clients = []
        self.logged_clients = {}
        
    def log(self, message):
        if LOG_ENABLED: 
            print(message)
    
    def start(self, address, port):
        """initialize the server socket using the specified address and port"""
        
        self.log("start")
        
        # create a socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # bind a socket        
        self.socket.bind((address, port))
        
        # listen to connections        
        self.socket.listen(MAX_QUEUED_CONNECTIONS)
        
    def run(self):
        """main loop"""
        
        self.log("run")
        
        while True:
            self.check_new_connections()
            if self.connected_clients or self.logged_clients:
                self.check_new_messages()
                
        # clean up
        self.socket.close()            
                
            
    def check_new_connections(self):
        """check for new client connections"""
                
        queued_connections = select.select([self.socket], [], [], TIMEOUT)[0] 
    
        # accept new connections
        for connection in queued_connections:
            self.log("new connection")
            
            # accept the new connection
            client_socket = connection.accept()[0]
                        
            # add it to the client sockets list
            self.connected_clients.append(client_socket)     
        
    def check_new_messages(self):
        """check for new messages from connected clients and logged clients, handles disconnections too"""        
        
        client_sockets_to_read = select.select(self.connected_clients + list(self.logged_clients.values()), [], [], TIMEOUT)[0]
        
        for client_socket in client_sockets_to_read:    
            self.log("client_sockets_to_read : {}".format(client_sockets_to_read))                    
            try:
                message = self.read_message(client_socket)                            
                if message:
                    self.log(message.decode(ENCODING))     
                    self.handle_message(message, client_socket)                   
                else:                                     
                    # the client has properly disconnected                            
                    self.remove_client(client_socket)
            except ConnectionResetError:
                # the client has abruptly disconnected 
                print("connection reset for socket {}".format(client_socket))
                self.close_client(client_socket)
                
    def remove_client(self, client_socket):
        """shutdown the socket then close it"""
        
        self.log("remove_client")
        
        client_socket.shutdown(socket.SHUT_WR)  
        self.close_client(client_socket)
                
    def close_client(self, client_socket):
        """close the socket and remove it from the list of connected clients and dictionary of logged clients"""
        
        self.log("close_client")
        
        client_socket.close()
        if client_socket in self.connected_clients: 
            self.log("removing connected client")
            self.connected_clients.remove(client_socket)
        if client_socket in self.logged_clients.values():
            self.log("removing logged client")  
            self.logged_clients = { login: socket for login, socket in self.logged_clients.items() if socket is not client_socket }
        
    def read_message(self, client_socket):
        """return the message read from the specified socket using the chat protocol, or None"""
        
        self.log("read_message")
            
        header = client_socket.recv(HEADER_LENGTH)
        if (header):
            # compute the body length from the header
            body_length = int(header.decode())        
            body = client_socket.recv(body_length)
            message = header + body        
            return message
        else:
            return None         
        
    def handle_message(self, message, client_socket):
        """deserialize a message and execute the code corresponding to its command"""
        
        self.log("handle_message")    
                 
        bodyBytes = message[HEADER_LENGTH:]
        body = bodyBytes.decode(ENCODING)
        tokens = body.split(DELIMITER)
        if tokens:
            command, *parameters = tokens
            if command == LOGIN:
                if parameters:
                    login = parameters[0]
                    self.log_user(client_socket, login)
            elif command == BROADCAST:            
                self.broadcast(message)
            elif command == WHISPER:       
                *_, dest = parameters     
                self.whisper(message, dest)
            else:
                print("unknown command {}".format(command)) 
        
            
    def log_user(self, client_socket, login):
        """log a user in, is the login is available"""
        
        self.log("log_user")
        
        success = False
        if login not in self.logged_clients:
            success = True
            self.log("login successful with name {} for client {}".format(login, client_socket))
            self.logged_clients[login] = client_socket
            self.connected_clients.remove(client_socket)
        else:
            self.log("login failure with name {} for client {}".format(login, client_socket))
            
        reply_command = LOGIN_REPLY + DELIMITER + str(success).lower() + DELIMITER + login        
        reply_message = self.serialize(reply_command)        
        client_socket.send(reply_message)
        
    
    
    def serialize(self, command):
        """create a message from a command"""
        length = len(command)      
        header = str(length).rjust(HEADER_LENGTH)
        return bytes(header + command, ENCODING)
        
    def broadcast(self, message):
        """broadcast a message to all connected clients"""        
        for socket in self.logged_clients.values():
            socket.send(message)
            
    def whisper(self, message, dest):
        """whisper a message to a specified client"""
        if dest in self.logged_clients:
            self.logged_clients[dest].send(message)
        else:
            self.log("dest {} not found in keys : {}".format(dest, self.logged_clients.keys()))
        
                 

# main code
chat_server= ChatServer()

chat_server.start('', 5555)

chat_server.run()

