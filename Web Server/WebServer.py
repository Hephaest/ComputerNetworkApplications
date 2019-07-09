#!/usr/bin/env python3
#-*-coding:utf-8-*-
# @Time    : 2018/11/25 14:41
# @Author  : Hephaest

from socket import *
from _thread import *
import sys

class StrProcess(str):
    """This class is used to split string on request line by " ".

    Attributes:
        str: the HTTP request socket receive from  client, which be converted
            into string type.
    """
    def __init__(self, str):
        """Inits StrProcess with str"""
        self.str = str

    def split_str(self):
        """Performs split_str operation"""
        spilt_list = []
        start = 0
        for i in range(len(self.str)):
            if self.str[i] == " ":
                spilt_list.append(self.str[start:i])
                start = i + 1
            if self.str[i] == "\r":
                break
        return spilt_list[1]


def handle_request(tcp_socket, client_ip, client_port):
    """Receive and response to HTTP request message.

    Args:
        :param tcp_socket: the socket which is created from start_server function.
        :param client_ip: IP address of the client.
        :param client_port: Port number of the client.

    Raises:
        FileNotFoundError: file does not exist.
    """
    print("Client ({ip}: {port}) is coming...".format(ip = client_ip, port = client_port))
    try:
        # 1. Receive request message from the client on connection socket.
        msg = tcp_socket.recv(1024).decode()
        if not msg:
            print("Error! server receive empty HTTP request.")
            tcp_socket.close()
        # Create new object (handlestr) from strProcess class.
        handle_str = StrProcess(msg)
        # 2. Extract the path of the requested object from the message (second part of the HTTP header).
        file_name = handle_str.split_str()[1:]
        # 3. Find the corresponding file from disk.
        # Check whether the requested object exists or not.
        f = open(file_name)
        f.close()
        # If object exists, ready to send "HTTP/1.1 200 OK\r\n\r\n" to the socket.
        status = "200 OK"
    except FileNotFoundError:
        # Else, ready to send "HTTP/1.1 404 Not Found\r\n\r\n" to the socket.
        status = "404 Not Found"
        file_name = "NotFound.html"
    re_header = "HTTP/1.1 " + status + "\r\n\r\n"
    # 4. Send the correct HTTP response.
    tcp_socket.send(re_header.encode())
    # 5. Store in temporary buffer.
    with open(file_name, 'rb') as f:
        file_content = f.readlines()
    # 6. Send the content of the file to the socket.
    for strline in file_content:
        tcp_socket.send(strline)
    # 7. Close the connection socket.
    print("Bye to Client ({ip}: {port})".format(ip = client_ip, port = client_port))
    tcp_socket.close()


def start_server(server_port, server_address):
    """Create a socket and wait for TCP connection at port [serverPort].

    The server is created as a multithreaded server and has a capacity of
    handling multiple concurrent connections.

    :param server_port: Configurable port, defined as an optional argument.
    """
    print("you can test the web server by accessing: ", end="")
    # For test
    print("http://" + server_address + ":" + str(server_port) + "/hello.html")
    print('Wait for TCP clients...')
    # 1. Create server socket
    server_socket = socket(AF_INET, SOCK_STREAM) #IPv4.
    # 2. Bind the server socket to server address and server port.
    server_socket.bind(("", server_port))
    # 3. Continuously listen for connections to server socket.
    server_socket.listen(5)
    while True:
        # 4. When a connection is accepted, call handleRequest function,
        # passing new connection socket
        connection_socket, (client_ip, client_port) = server_socket.accept()
        # Run multithreaded method
        start_new_thread(handle_request, (connection_socket, client_ip, client_port))
    # 5. Close server socket.
    server_socket.close()  # server is always waiting and never close.


# Start here.
server_port = int(sys.argv[1])
server_address = gethostbyname(gethostname())
start_server(server_port, server_address)