import socket

# create a socket
my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# bind a socket
my_socket.bind(('', 5555))

# listen to connections
max_queued_connections = 5
my_socket.listen(max_queued_connections)

# accept connections
connection, address = my_socket.accept()
