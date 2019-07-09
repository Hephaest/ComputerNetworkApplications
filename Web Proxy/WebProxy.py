#!/usr/bin/env python3
#-*-coding:utf-8-*-
# @Time    : 2018/11/25 17:40
# @Author  : Hephaest


from socket import *
import os
import sys

host = ""  # global variable.

class StrProcess(str):
    """This class is used to split string on request line by " ".

    Attributes:
        str: the HTTP request socket receive from  client, which be converted
             into string type.
    """
    def __init__(self, str):
        """Inits StrProcess with str."""
        self.str = str

    def split_str(self):
        """Perform split_str operation."""
        spilt_list = []
        start = 0
        for i in range(len(self.str)):
            if self.str[i] == " ":
                spilt_list.append(self.str[start:i])
                start = i + 1
            if self.str[i] == "\r":
                break
        try:
            return spilt_list[0],spilt_list[1]
        except IndexError:
            return None

    def get_cmd_type(self):
        """Extract method type from HTTP request line."""
        return self.split_str()[0]

    def get_body(self):
        """Extract entity body from HTTP request message body."""
        body_start = self.str.find('\r\n\r\n') + 4
        return self.str[body_start:]

    def get_referer(self):
        """Extract referer from HTTP request header lines."""
        ref_pos = self.str.find('Referer: ') + 9
        ref_stop = self.str.find('\r\n', ref_pos+1)
        get_ref = self.str[ref_pos:ref_stop]
        get_ref_start = get_ref.find('9/') + 2
        get_ref_path = self.str[ref_pos+get_ref_start:ref_stop]
        return get_ref_path

    def get_path(self):
        """Extract URL from HTTP request request line."""
        original_path = self.split_str()[1]
        for i in range(len(original_path)):
            if original_path[i] == "/":
                original_path = original_path[i+1:]
                return original_path

    def change_name(self):
        """Convert all special symbols to "-"."""
        original_name = self.get_path()
        for i in range(len(original_name)):
            if original_name[i] == "/" or original_name[i] == "?" \
                    or original_name[i] == "=" or original_name[i] == "&" \
                    or original_name[i] == "%":
                original_name = original_name[:i] + "-" + original_name[i+1:]
        return original_name

    def get_hostname(self):
        """Extract host name from URL."""
        whole_URL = self.get_path()
        for i in range(len(whole_URL)):
            if whole_URL[i] == "/":
                    host_name = whole_URL[:i]
                    return host_name
        return whole_URL


def start_listen(tcp_socket, client_ip, client_port):
    """ Receive HTTP request message and retrieve the object from cache or server.

    This function could handle different HTTP request message. Especially for
    "Get" method type, proxy will firstly try to find the requested object from
    cache, if not found, proxy than forward the HTTP request message to server
    and then forward the HTTP response message to browser and store the message
    in the cache as well. In addition, "DELETE" method also need to whether the
    object in the cache or not.

    Be careful! The file should be opened in binary mode because we possibly need
    to write or read special type of object, for instance, .jpg, .svg, etc.

    Args:
        :param tcp_socket: the socket which is created from start_server function.
        :param client_ip: IP address of the client.
        :param client_port: Port number of the client.

    Raises:
        IOError, FileNotFoundError: file does not exist.
        ConnectionResetError: client refresh the browser while server still send message.
        TypeError: input format is wrong or empty.
        socket.gaierror: Host name might be wrong.
    """
    # 1. Receive request message from the client on connection socket.
    message = tcp_socket.recv(1024).decode()
    # Create new object (handle_str) from StrProcess class.
    handle_str = StrProcess(message)
    print("client is coming: {addr}:{port}".format(addr = client_ip, port = client_port))
    file_error = False
    global host
    try:
        command = handle_str.get_cmd_type()
        # 2. Extract the path of the requested object from the message (second part of the HTTP header).
        filename = handle_str.change_name()
        # 3. Find the specific method type and handle the request.
        if command == "DELETE" :
            # Delete the object if it exists in cache.
            os.remove("./Cache/" + filename)
            tcp_socket.send(b"HTTP/1.1 200 OK\r\n\r\n")
            print("File is removed.")
        elif command == "GET" or command == "HEAD":
            print("Client want to {c} the {o}.".format(c=command, o=filename))
            # Check whether the requested object exists or not.
            f = open("./Cache/" + filename, "rb")
            file_content = f.readlines()
            f.close()
            if command == "GET":
                print("File in cache!")
                # Find the corresponding file from disk if it exists.
                for i in range(0, len(file_content)):
                    tcp_socket.send(file_content[i])  # Send HTTP response message.
            else:  # "HEAD" method.
                list_to_str = ""
                for i in range(0, len(file_content)):
                    list_to_str += file_content[i].decode()
                HTTP_header_end = list_to_str.find("\r\n\r\n")
                # Only send HTTP response message header lines.
                tcp_socket.send(list_to_str[:HTTP_header_end + 4].encode())
        elif command == "PUT" or command == "POST":  # Only implement upload files.
            f = open("./Cache/" + filename, "ab")
            f.write(b"HTTP/1.1 200 OK\r\n\r\n" + handle_str.get_body().encode())
            f.close()
            print("Update successfully!")
            tcp_socket.send(b"HTTP/1.1 200 OK\r\n\r\n")
            body_re = b"true" if command == "PUT" else handle_str.get_body().encode()
            tcp_socket.send(body_re)
        else:
            tcp_socket.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
    # 4. If file doesn't exist in the cache, handle exceptions.
    except (IOError, FileNotFoundError):
        if command == "GET":
            # Create a socket on the proxy server.
            c = socket(AF_INET, SOCK_STREAM)
            hostname = handle_str.get_hostname()
            file = handle_str.split_str()[1]
            print("File isn't in the cache!")
            try:
                # Connect to the socket at port 80.
                c.connect((hostname, 80))
                host = hostname  # record the real hostname.
                request = "GET " + "http:/" + file + " HTTP/1.1\r\n\r\n"
            except:
                try:
                    # Need to use the global host or referer hostname.
                    new_host = handle_str.get_referer() if host == "" else host
                    c.connect((new_host, 80))
                    request = "GET " + "http://" + new_host + file + " HTTP/1.1\r\n\r\n"
                except:
                    tcp_socket.send(b"HTTP/1.1 404 Not Found\r\n\r\n")
                    with open("./Cache/NotFound.html", 'rb') as f:
                        file_content = f.readlines()
                    for strline in file_content:
                        tcp_socket.send(strline)
                    file_error = True
            if file_error is False:
                c.sendall(request.encode())
                # Read the response into buffer.
                print("proxyserver have found the host.")
                # Create a new file in the cache for the requested file.
                # Also send the response in the buffer to client socket
                # and the corresponding file in the cache.
                writeFile = open("./Cache/" + filename, "wb")
                print("Poxy server is receiving data...")
                # Receive HTTP response message until all messages are received.
                while True:
                    data = c.recv(4096)
                    if not data:
                        break
                    sys.stdout.write(">")
                    # Send the content of the file to the socket.
                    tcp_socket.sendall(data)
                    writeFile.write(data)
                writeFile.close()
                sys.stdout.write("100%\n")
            c.close()
        elif command == "DELETE":
            tcp_socket.send(b"HTTP/1.1 204 Not Content\r\n\r\n")
    except (ConnectionResetError, TypeError):
        print("Bye to client: {addr}:{port}".format(addr = client_ip, port = client_port))
    # Close the client socket.
    print("tcp socket closed\n")
    tcp_socket.close()


def start_server(port):
    """Create a socket and wait for TCP connection at port [Port].

    :param port: Configurable port, defined as an optional argument.
    """
    # 1. Create server socket
    server_socket = socket(AF_INET, SOCK_STREAM)  # In IPv4
    # 2. Bind the server socket to server address and server port
    server_socket.bind(("", port))
    # 3. Continuously listen for connections to server socket
    server_socket.listen(5)
    while True:
        # 4. When a connection is accepted, call start_listen function,
        # Passing new connection socket.
        connection_socket, (client_ip, client_port) = server_socket.accept()
        print('wait for request:')
        start_listen(connection_socket, client_ip, client_port)
    # 5. Close server socket.
    server_socket.close()  # In fact, proxy is always waiting for request.


# Start here.
print('Wait for TCP clients...')
start_server(int(sys.argv[1]))