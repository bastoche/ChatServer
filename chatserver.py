import socket
import select


# create a socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# bind a socket
port = 5555
server_socket.bind(('', port))

# listen to connections
max_queued_connections = 5
server_socket.listen(max_queued_connections)


client_sockets = []
timeout = 0.05 # 50 milliseconds


# main loop
while True:
    # check for new connections
    queued_connections, wlist, xlist = select.select([server_socket], [], [], timeout)
    
    # accept new connections
    for connection in queued_connections:
        print("new connection !")
        # accept the new connection
        client_socket, address = connection.accept()
        # add it to the client sockets list
        client_sockets.append(client_socket)        
        
    # check for new commands if there are clients connected 
    if client_sockets:        
        # print("connected clients : {}".format(len(client_sockets)))
        client_sockets_to_read, wlist, xlist = select.select(client_sockets, [], [], timeout)
        
        for client_socket in client_sockets_to_read:
            print("new message to read")            
            message = client_socket.recv(1024)
            print("received message {} with length {}".format(message.decode(), len(message)))            
            if message:
                # the message is not empty, send back the received message
                client_socket.send(message)                
            else:                
                # close the socket
                client_socket.shutdown(socket.SHUT_WR)                
                client_socket.close()
                client_sockets.remove(client_socket)
                
            
        
    
server_socket.close()

