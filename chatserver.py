import socket
import select

# character encoding
ENCODING = "cp850"

# socket parameters
MAX_QUEUED_CONNECTIONS = 5

# chat protocol
LENGTH = 512
HEADER_LENGTH = 4
MAX_BODY_LENGTH = LENGTH - HEADER_LENGTH
DELIMITER = '\n'

# chat commands 
BROADCAST = "broadcast"
LIST_USERS = "list_users"
LOGIN = "login"
LOGIN_REPLY = "login_reply"
REPLY_USERS = "reply_users"
WHISPER = "whisper"

# for debug purposes
LOG_ENABLED = True
ERROR_ENABLED = True

class ChatServer:

    
    def __init__(self):
        self.server_socket = None 
        self.connected_clients = []
        self.logged_clients = {}
        
    def log(self, message):
        if LOG_ENABLED: 
            print(message)
            
    def error(self, message):
        if ERROR_ENABLED: 
            print(message)
    
    def start(self, address, port):
        """initialize the server socket using the specified address and port"""
        
        self.log("start")
        
        # create a socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # bind a socket        
        self.server_socket.bind((address, port))
        
        # listen to connections        
        self.server_socket.listen(MAX_QUEUED_CONNECTIONS)
        
    def run(self):
        """main loop : accepts incoming connections and receive messages"""
        
        self.log("run")
        
        while True:
            sockets_to_read = select.select([self.server_socket] + self.connected_clients + list(self.logged_clients.values()), [], [])[0]            
            
            self.log("sockets_to_read : {}".format(sockets_to_read))
            
            for socket in sockets_to_read:                 
                if socket is self.server_socket:
                    self.log("new connection")
                    # accept the new connection
                    client_socket = socket.accept()[0]
                    # add it to the client sockets list
                    self.connected_clients.append(client_socket)     
                else:
                    self.log("new message")          
                    try:
                        message = self.read_message(socket)                            
                        if message:
                            self.log(message.decode(ENCODING))     
                            self.handle_message(message, socket)                   
                        else:                                     
                            # the client has properly disconnected                            
                            self.close_client(socket)
                    except ConnectionResetError:
                        # the client has abruptly disconnected 
                        self.error("connection reset for socket {}".format(socket))
                        self.close_client(socket)
                
        # clean up
        self.server_socket.close()            
                
                
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
            self.log("received empty header")
            return None         
        
    def handle_message(self, message, client_socket):
        """deserialize a message and execute the code corresponding to its command"""
        
        self.log("handle_message")    
                 
        bodyBytes = message[HEADER_LENGTH:]
        body = bodyBytes.decode(ENCODING)
        tokens = body.split(DELIMITER)
        if tokens:
            command, *parameters = tokens
            if command == BROADCAST:            
                self.broadcast(message)
            elif command == LIST_USERS:            
                self.send_logged_clients(client_socket)
            elif command == LOGIN:
                if parameters:
                    login = parameters[0]
                    self.log_user(client_socket, login)         
                else:
                    self.error("login without parameters")   
            elif command == WHISPER:       
                if parameters:
                    *_, dest = parameters     
                    self.whisper(message, dest)
                else:
                    self.error("whisper without parameters")
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
            
        login_reply_command = LOGIN_REPLY + DELIMITER + str(success).lower() + DELIMITER + login        
        login_reply_message = self.serialize(login_reply_command)   
        if login_reply_message:     
            client_socket.send(login_reply_message)   
        else:
            self.error("unable to serialize login reply")
    
    def serialize(self, command):
        """returns the command serialized as a bytes object, or None if the command is too long"""
        length = len(command)      
        if length <= MAX_BODY_LENGTH:
            header = str(length).rjust(HEADER_LENGTH)
            return bytes(header + command, ENCODING)
        else:
            return None
        
    def broadcast(self, message):
        """broadcast a message to all connected clients"""        
        for client_socket in self.logged_clients.values():
            client_socket.send(message)
            
    def whisper(self, message, dest):
        """whisper a message to a specified client"""
        if dest in self.logged_clients:
            self.logged_clients[dest].send(message)
        else:
            self.log("dest {} not found in keys : {}".format(dest, self.logged_clients.keys()))
            
    def send_logged_clients(self, client_socket):
        """send the list of logged clients names to a specified client"""
        logins = ', '.join(list(self.logged_clients.keys()))
        reply_users_command = REPLY_USERS + DELIMITER + logins
        reply_users_message = self.serialize(reply_users_command)
        if reply_users_message:        
            client_socket.send(reply_users_message) 
        else:
            self.error("unable to serialize list of logged clients")
                         
# main code
chat_server= ChatServer()

chat_server.start('', 5555)

chat_server.run()

