#!/usr/bin/env python3
#-*-coding:utf-8-*-
# @Time    : 2018/11/25 16:23
# @Author  : Hephaest

from socket import *
import sys

# 1. Set the web server's address.
host_port = int(sys.argv[1])
host_address = gethostbyname(gethostname())
# 2. Create client socket to initiate TCP connection to web server.
tcp_client = socket(AF_INET, SOCK_STREAM)
tcp_client.connect((host_address, host_port))
# 3. Enter the file client want to query the web server.
print("Hello, which document do you want to query?")
while True:
    obj = input("I want to query: ")
    # 4. Send the HTTP request message.
    message = "GET /" + obj + " HTTP/1.1\r\n" \
            "Host: " + host_address + ":" + str(host_port) + "\r\n" \
            "Connection: close\r\n" \
            "Upgrade-Insecure-Requests: 1\r\n" \
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36\r\n" \
            "DNT: 1\r\n" \
            "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\r\n" \
            "Accept-Encoding: gzip, deflate\r\n" \
            "Accept-Language: zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7\r\n\r\n"
    tcp_client.send(message.encode())
    while True:
        # 5. Receive HTTP response message and print it to the console.
        data = tcp_client.recv(1024)
        if not data:
            break
        print("Web server responded to your request:")
        print(data.decode())
    tcp_client.close() # close current connection.
    # 6. ask the client whether it wants to continue.
    ans = input('\nDo you want to cut this connection(y/n) :')
    if ans == 'y' or ans == 'Y':
        break
    elif ans == 'n' or ans == 'N':
        # Try again.
        print("Anything else I can help you?")
        tcp_client = socket(AF_INET, SOCK_STREAM)
        tcp_client.connect((host_address, host_port))
    else:
        print("Command Error, quit.")
        break