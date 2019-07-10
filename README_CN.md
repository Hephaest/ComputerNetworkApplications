目录
=================
   * [Python 实现网络应用程序开发](#python-实现网络应用程序开发)
   * [ICMP Ping](#icmp-ping)
      * [目的](#目的)
      * [原理](#原理)
      * [函数实现](#函数实现)
      * [Result](#result)
   * [路由追踪](#路由追踪)
      * [目的](#目的-1)
      * [原理](#原理-1)
      * [函数实现](#函数实现-1)
      * [Result](#result-1)
   * [Web服务器](#web服务器)
      * [目的](#目的-2)
      * [原理](#原理-2)
      * [函数实现](#函数实现-2)
      * [Result](#result-2)
         * [WebServer.py](#webserverpy)
         * [Client.py](#clientpy)
   * [Web代理服务器](#web代理服务器)
      * [目的](#目的-3)
      * [原理](#原理-3)
      * [函数实现](#函数实现-3)
      * [Result](#result-3)
         * [Browser Test](#browser-test)
         * [WebProxy.py](#webproxypy)

         
# Python 实现网络应用程序开发
[![LICENSE](https://img.shields.io/cocoapods/l/AFNetworking.svg)](https://github.com/Hephaest/ComputerNetworkApplications/blob/master/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.6.7-%237000FF.svg)](https://www.python.org/downloads/release/python-367/)

[English](README.md) | 中文

最后一次更新于 `2019/07/10`

该项目旨在提高您开发基于套接字的应用程序的能力。
# ICMP Ping
## 目的
此任务是重新创建第3讲(延迟，丢失和吞吐量)中讨论的ping客户端。
Ping 是一个用于在计算机网络中测量延迟和丢失的工具。
在实际应用中，我们可以通过 `ping` 命令分析判断网络失败的原因。当然，这类信息也可用于帮助我们选择性能更佳的IP地址作为代理服务器。
## 原理
Ping 通常使用 **Internet 控制消息协议** (**ICMP**) 报文来测量网络中的延迟和丢失：本机在 ICMP 包中发送回响请求(ICMP类型代码为8)给另一个主机。然后，主机解包数据包并提取ICMP类型代码并匹配请求和回复之间的ID。如果远程主机的响应报文ICMP类型代码为0，然后我们可以计算发送请求和接收回复之间经过的时间，进而精确的计算两台主机之间网络的延迟。

**注意**: IP数据报和ICMP错误代码的结构(ICMP类型代码为3)如下所示。因特网校验和也是数据包的重要部分，但它不是本函数实现的核心。
<p align="center"><img src ="images/f1.jpg" width = "500px"></p>
<p align="center"><img src ="images/f2.jpg"></p>

## 函数实现
基于上述原理，首先，需要创建一个与协议ICMP关联的套接字，并设置超时以控制用于接收数据包的时间套接字。
```Python
# 运行特权TCP套接字，1是与协议ICMP关联的套接字模块常量。
icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, 1)
icmp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeout)
```
创建套接字后，需要实现一个函数来构建，打包并将ICMP数据包发送到目标主机。
如图所示，如果创建一个32字节大小的数据包，那么只有四个字节长度来存储有效负载数据。
因此，以浮点格式（4个字节）存储当前时间帧是比较好的解决办法。
但是，由于精度损失，不能使用此数据来计算总网络延迟。 
"!" 但是，由于精度损失，我永远不会使用此数据来计算总网络延迟。

构建和打包ICMP数据包源代码：
```Python
def receive_one_ping(icmp_socket, port_id, timeout, send_time):
    while True:
        # 1. 等待套接字并得到回复。
        wait_for_data = select.select([icmp_socket], [], [], timeout)
        # 2. 一旦接受，记录当前时间。
        data_received = time.time()
        rec_packet, addr = icmp_socket.recvfrom(1024)
        ip_header = rec_packet[8: 12]
        icmp_header = rec_packet[20: 28]
        payload_size = struct.calcsize("!f")
        # 3. 解压包首部行查找有用的信息。
        type, code, checksum, id, sequence = struct.unpack("!bbHHh", icmp_header)
        # 4. 检查收发之间的 ID 是否匹配。
        if type == 0 and id == port_id:  # type should be 0
            ttl = struct.unpack("!b", ip_header[0:1])[0]
            delay_time = data_received - send_time
        # 5. 返回比特大小，延迟率和存活时间。
            return payload_size * 8, delay_time, ttl
        elif type == 3 and code == 0:
            return 0  # 网络无法到达的错误。
        elif type == 3 and code == 1:
            return 1  # 主机无法到达的错误。
```
当从同一主机获得所有ping测试结果时，需要另一个函数来显示所有测量的最小时间，平均时间和最大延迟。
```Python
def ping_statistics(list):
    max_delay = list[0]
    mini_delay = list[0]
    sum = 0
    for item in list:
        if item >= max_delay:
            max_delay = item
        elif item <= mini_delay:
            mini_delay = item
        sum += item
    avg_delay = int(sum / (len(list)))
    return mini_delay, max_delay, avg_delay
```
最后一件事是处理异常。需要处理不同的ICMP错误代码和返回值的超时。代码如下所示：
```Python
def ping(host, count_num="4", time_out="1"):
    # 1. 查找主机名，将其解析为IP地址。
    ip_addr = socket.gethostbyname(host)
    successful_list = list()
    lost = 0
    error = 0
    count = int(count_num)
    timeout = int(time_out)
    timedout_mark = False
    for i in range(count):  # i 是序列的值
        # 打印报文首部行
        ......
        try:
            # 2. 调用 doOnePing 函数。
            ping_delay = do_one_ping(ip_addr, timeout, i)
            # 3. 打印出返回的延迟信息。
            if ping_delay == 0 or ping_delay == 1:
                # 获取本机的 IP 地址。
                ip_addr = socket.gethostbyname(socket.gethostname())
                print("Reply from {ipAdrr}: ".format(ipAdrr = ip_addr), end = "")
                result = "Destination host unreachable." if ping_delay == 0 else \
                         "Destination net unreachable."
                print(result)
                error += 1
            else:
                bytes, delay_time, ttl = ping_delay[0], int(ping_delay[1] * 1000), \
                                         ping_delay[2]
                print("Reply from {ipAdrr}: ".format(ipAdrr = ip_addr), end = "")
                # 如果可以成功接收数据包，
                # 在list里追加延迟时间。
                successful_list.append(delay_time)
                # 如果延迟时间小于 1 ms，则记为0。
                ......
        except TimeoutError:  # 超时类型
            lost += 1
            print("Request timed out.")
            # 如果它不总是超时的情况，
            # 我们需要计算最大延迟时间。
            if timedout_mark is False:
                timedout_mark = True
        time.sleep(1)  # 每秒。
    #  4. 继续执行直到结束。
    ......
```
## Result
```
C:\Users\asus\Desktop\lab_solution\ICMP Ping>ICMPPing.py>ping www.baidu.com
Pinging www.baidu.com [111.13.100.92] with 32 of data:
Reply from 111.13.100.92: bytes = 32 time = 28ms TTL = 51.
Reply from 111.13.100.92: bytes = 32 time = 35ms TTL = 51.
Reply from 111.13.100.92: bytes = 32 time = 33ms TTL = 51.
Reply from 111.13.100.92: bytes = 32 time = 31ms TTL = 51.

Ping statistics for 111.13.100.92:
    Packet: Sent = 4, Received = 4, lost = 0 (0% loss).
Approximate round trip times in milli - seconds:
    Minimum = 28ms, Maximum = 35ms, Average = 31ms.

C:\Users\asus\Desktop\lab_solution\ICMP Ping>ICMPPing.py>ping google.com
Pinging google.com [172.217.161.174] with 32 of data:
Request timed out.
Request timed out.
Request timed out.
Request timed out.

Ping statistics for 172.217.161.174:
    Packet: Sent = 4, Received = 0, lost = 4 (100% loss).
C:\Users\asus\Desktop\lab_solution\ICMP Ping>ICMPPing.py>ping www.baidu.com -n 6
Pinging www.baidu.com [111.13.100.92] with 32 of data:
Reply from 111.13.100.92: bytes = 32 time = 29ms TTL = 51.
Reply from 111.13.100.92: bytes = 32 time = 46ms TTL = 51.
Reply from 111.13.100.92: bytes = 32 time = 33ms TTL = 51.
Reply from 111.13.100.92: bytes = 32 time = 44ms TTL = 51.
Reply from 111.13.100.92: bytes = 32 time = 36ms TTL = 51.
Reply from 111.13.100.92: bytes = 32 time = 35ms TTL = 51.

Ping statistics for 111.13.100.92:
    Packet: Sent = 6, Received = 6, lost = 0 (0% loss).
Approximate round trip times in milli - seconds:
    Minimum = 29ms, Maximum = 46ms, Average = 37ms.

C:\Users\asus\Desktop\lab_solution\ICMP Ping>ICMPPing.py>ping www.baidu.com -n 6 -w 2
Pinging www.baidu.com [111.13.100.92] with 32 of data:
Reply from 111.13.100.92: bytes = 32 time = 25ms TTL = 51.
Reply from 111.13.100.92: bytes = 32 time = 35ms TTL = 51.
Reply from 111.13.100.92: bytes = 32 time = 20ms TTL = 51.
Reply from 111.13.100.92: bytes = 32 time = 55ms TTL = 51.
Reply from 111.13.100.92: bytes = 32 time = 34ms TTL = 51.
Reply from 111.13.100.92: bytes = 32 time = 37ms TTL = 51.

Ping statistics for 111.13.100.92:
    Packet: Sent = 6, Received = 6, lost = 0 (0% loss).
Approximate round trip times in milli - seconds:
    Minimum = 20ms, Maximum = 55ms, Average = 34ms.
```
# 路由追踪
## 目的
此任务是重新创建第3讲(延迟，丢失和吞吐量)中的路由追踪工具。这用于测量主机和到达目的地的路径上的每一跳之间的延迟。在实际应用中，路由追踪可以找到源主机和目标主机之间的路由器以及到达每个路由器所需的时间。
## 原理
<p align="center"><img src ="images/f3.jpg"></p>

如上图所示，源主机使用ICMP echo请求报文，但有一个重要的修改：
**存活时间**(**TTL**)的值初始为1。这可以确保我们从第一跳获得响应。 一旦报文到达路由器，TTL计数器就会递减。 
当TTL达到0时，报文将返回到源主机，ICMP 类型为11(已超出TTL且IP数据报尚未到达目标并被丢弃)。
每次增加TTL都会重复此过程，直到我们收到回复。如果echo回复ICMP类型为0，则表示IP数据报已到达目的地。
然后我们就可以停止运行路由追踪的脚本了。在此过程中，可能会发生异常并且我们需要处理错误代码与 ICMP Ping 相同。
## 函数实现
基于上述原理，首先，除了创建一个与协议ICMP关联的套接字并设置超时来控制用于接收数据包的套接字外，还需要通过
`socket.setsockopt(level, optname, value)` 函数设置套接字的TTL。
```Python
client_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, 1) # ICMP
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO , time_out)
client_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))
```
创建套接字后，需要实现一个函数来构建，打包并将ICMP数据包发送到目标主机。这部分代码和在 ICMP Ping 中的**构建和打包ICMP数据包源代码**一致。

下一步是等待并收到回复。套接字将一直等待，直到收到数据包或达到超时限制。 通过 ICMP 回响报文发现并报告*无法访问目标主机*和*无法访问目标网路*。这部分和**接受数据包源码**相似但路由追踪需要额外记录每次访问到路由器的IP地址。代码如下所示：
```Python
def receive_one_trace(icmp_socket, send_time, timeout):
    try:
        # 1. 等待套接字并得到回复。
        ... Similar to Receive Packet Source ...
        # 2. 一旦接受，记录当前时间。
        rec_packet, retr_addr = icmp_socket.recvfrom(1024)
        # 3. 解压包首部行查找有用的信息。
        ... Similar to Receive Packet Source ...
        # 4. 通过代号类型检查数据包是否丢失。
        ... Similar to Receive Packet Source ...
    except TimeoutError :
        print_str = "*   "  # 超时。
    finally:
        ..... # 打印延迟时间。
    # 返回当前路由器的IP地址。
    # 如果超时的话，直接返回字符串。
    try:
        retre_ip = retr_addr[0]
    except IndexError:
        retre_ip = "Request timeout"
    finally:
        return retre_ip
```
最后一件事是为每个路由器实现重复测量，解析在对各自主机名的响应中找到的IP地址并处理异常。代码如下所示：
```Python
def trace_route(host, timeout=2):
    # 可配置超时，使用可选参数设置。
    # 1. 查找主机名，将其解析为IP地址。
    ip_addr = socket.gethostbyname(host)
    ttl = 1
    print("Over a maximum of {max_hop} hops:\n".format(max_hop = MAX_HOP))
    print("Tracing route to " + host + " [{hostIP}]:".format(hostIP = ip_addr))
    for i in range(MAX_HOP):
        sys.stdout.write("{0: >3}".format(str(ttl) + "\t"))
        cur_addr = do_three_trace(ip_addr, ttl, i, timeout)
        try:
            sys.stdout.write("{0:<}".format(" " + socket.gethostbyaddr(cur_addr)[0] + " [" + cur_addr + "]" + "\n"))
        except (socket.herror, socket.gaierror):
            sys.stdout.write("{0:<}".format(" " + cur_addr + "\n"))
        if cur_addr == ip_addr :
            break
        ttl += 1
    sys.stdout.write("\nTrace complete.\n\n")
```
## Result
```
Over a maximum of 30 hops:
    Tracing route to www.baidu.com [111.13.100.91]:
    1 16 ms 15 ms 15 ms 10.129.0.1
    ...... # All successful
    5 * * * Request timeout
    6 * * * Request timeout
    ...... # All successful
    9 * * * Request timeout
    ...... # All successful
    13 * * * Request timeout
    14 22 ms 22 ms 21 ms 111.13.100.91
    Trace complete.

C:\Users\asus\Desktop\lab_solution\Traceroute>Traceroute.py>tracert 10.129.21.147
Over a maximum of 30 hops:
Tracing route to 10.129.21.147 [10.129.21.147]:
 1 Host unreachable * Host unreachable DESKTOP-6VPPJQ8 [10.129.34.15]
 2        * Host unreachable     *     DESKTOP-6VPPJQ8 [10.129.34.15]
 ...... All situations are the same
29 Host unreachable * Host unreachable DESKTOP-6VPPJQ8 [10.129.34.15]
30        * Host unreachable     *     DESKTOP-6VPPJQ8 [10.129.34.15]
Trace complete.
```
# Web服务器
## 目的
此任务是构建一个简单的HTTP Web服务器。根据第4讲(Web 和 HTTP)中学习到的知识，Web 服务器是Internet的基础部分，它们提供我们熟悉的网页和内容。
网页由对象组成，这些对象可以是HTML文件，JPEG图像，Java小程序等。HTTP流量通常绑定到端口80，端口8080是常用的替代方案。因此，虚拟主机（机器）使用本地端口号80和8080。
## 原理
HTTP/1.1 含有许多类型的 HTTP 请求，在本任务中，只考虑 HTTP GET 请求。
如下图所示，一个简单的 web 服务器从前端接受 HTTP 请求报文。收到此请求后，简单 Web 服务器将从邮件中提取所请求对象的路径，然后尝试从硬盘中检索请求的对象。如果它成功找到硬盘中的对象，它会将对象发送回具有相应首部行的客户端(其中包含Status-Code 200)。否则，它将使用HTTP响应报文（将包含404 Not Found"状态将"Not Found"网页发送到客户端。
line)". HTTP 请求和响应报文的格式已在下图5.(a)和5.(b)显示。
<p align="center"><img src ="images/f4.jpg" width = "600px"></p>
<p align="center"><img src ="images/f5.png" width = "600px"></p>

## 函数实现
基于上述原理，首先，创建一个支持 IPv4 的套接字并将其绑定在高于1024的端口上。Web服务器应该同时监听5个请求，并具有处理多个并发连接的能力。

Web 服务器运行源码：
```Python
def start_server(server_port , server_address):
    # 将 web 服务器绑定到可配置端口，定义为可选参数。
    # 1. 常见一个服务器套接字。
    server_socket = socket(AF_INET, SOCK_STREAM) #IPv4
    # 2. 将服务器套接字绑定到服务器地址和服务器端口。
    server_socket.bind(("", server_port))
    # 3. 持续监听与服务器套接字的连接。
    server_socket.listen(5)
    while True:
        # 4. 当接受连接时，调用 handleRequest 函数，传递新的连接套接字。
        connection_socket , (client_ip, client_port) = server_socket.accept()
        # 创建一个多线程服务器实现，能够处理多个并发连接。
        start_new_thread(handle_request , (connection_socket , client_ip, client_port))
     # 5. 关闭服务器端的套接字。
     server_socket.close() # 不然服务器会一直监听，不会主动关闭。

 # 从这里开始运行。
 server_port = int(sys.argv[1])
 server_address = gethostbyname(gethostname())
 start_server(server_port)
```
创建套接字后，web 服务器需要处理HTTP GET请求。在处理之前，创建了一个StrProcess类来重写字符串模块中的split方法。用空格分割一个字符串，只处理请求行。因此，当它找到字符"\r"时，它将停止处理并返回结果。

StrProcess 类源码:
```Python
class StrProcess(str):
    def __init__(self, str):
        """用字符型变量 str 初始该属性"""
        self.str = str
    def split_str(self):
        """实现分割操作"""
        spilt_list = []
        start = 0
        for i in range(len(self.str)):
            if self.str[i] == " ":
                spilt_list.append(self.str[start:i])
                start = i + 1
            if self.str[i] == "\r":
                break
        return spilt_list[1]
```
最后一件事是处理 HTTP GET 请求和异常。由于非持久性HTTP，不需要在true循环时写入以接收HTTP请求报文。如果套接字收到空报文，则应该关闭它。否则，web 服务器需要检查对象是否存在于缓存中。如果对象存在，则使用"HTTP/1.1 200 OK \r\n\r\n"将对象发送到客户端，否则发生"FileNotFoundError"异常，然后对于"未找到"的HTML文件使用"HTTP/1.1 404 Not Found\r\n\r\n"发送到客户端。 发送HTTP响应报文后，HTTP服务器将关闭TCP连接。代码如下所示：
```Python
def handle_request(tcp_socket, client_ip, client_port):
    print("Client ({ip}: {port}) is coming...".format(ip = client_ip, port = client_port))
    try:
        # 1. 在连接套接字上从客户端接收请求报文。
        msg = tcp_socket.recv(1024).decode()
        if not msg:
            print("Error! server receive empty HTTP request.")
            tcp_socket.close()
        # 从strProc类创建新对象(handlestr)。
        handle_str = StrProcess(msg)
        # 2. 从报文中提取所请求对象的路径(HTTP 首部行的第二部分)。
        file_name = handle_str.split_str()[1:]
        # 3. 从磁盘中查找相应的文件。
        # 检查请求的对象是否存在。
        f = open(file_name)
        f.close()
        # 如果对象存在，准备发送 "HTTP/1.1 200 OK\r\n\r\n" 到套接字。
        status = "200 OK"
    except FileNotFoundError:
        # 否则，准备发送 "HTTP/1.1 404 Not Found\r\n\r\n" 到套接字。
        status = "404 Not Found"
        file_name = "NotFound.html"
    re_header = "HTTP/1.1 " + status + "\r\n\r\n" # 最后一个''\r\n'' 意味着头报文的结束。
    # 4. 发送正确的HTTP响应。
    tcp_socket.send(re_header.encode())
    # 5. 存储在临时缓冲区中
    with open(file_name, 'rb') as f:
        file_content = f.readlines()
    # 6. 将文件的内容发送到套接字。
    for strline in file_content:
        tcp_socket.send(strline)
    # 7. 关闭连接的套接字。
    print("Bye to Client ({ip}: {port})".format(ip = client_ip, port = client_port))
    tcp_socket.close()
```
编写了一个单独的HTTP客户端来查询 web 服务器。此客户端可以发送 HTTP GET 请求并在控制台上接收HTTP响应报文。该程序的优点是它只需输入对象的名称或选择保留或离开即可查询对象。

HTTP 客户端源码：
```Python
from socket import *
import sys

# 1. 设置 web 服务器的地址。
host_port = int(sys.argv[1])
host_address = gethostbyname(gethostname())
# 2. 创建客户端套接字以启动与 web 服务器的 TCP 连接。
tcp_client = socket(AF_INET, SOCK_STREAM)
tcp_client.connect((host_address , host_port))
# 3. 输入要查询 web服务器的文件客户端。
print("Hello, which document do you want to query?")
while True:
    obj = input("I want to query: ")
    # 4. 发送 HTTP 请求报文。
    message = "GET /" + obj + " HTTP/1.1\r\n" \
              "Host: " + host_address + ":" + str(host_port) + "\r\n" \
              "Connection: close\r\n" \
              "Upgrade-Insecure-Requests: 1\r\n" \
              "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36\r\n" \
              ...... # 首部行。
              "Accept-Language: zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7\r\n\r\n"
    tcp_client.send(message.encode())
    while True:
        # 5. 接收HTTP响应报文并将其打印到控制台。
        data = tcp_client.recv(1024)
        if not data:
            break
        print("Web server responded to your request:")
        print(data.decode())
    tcp_client.close() # 关闭当前的连接。
    # 6. 询问客户是否要继续。
    ans = input('\nDo you want to cut this connection(y/n) :')
    if ans == 'y' or ans == 'Y':
        break
    elif ans == 'n' or ans == 'N':
        # 重新尝试。
        print("Anything else I can help you?")
        tcp_client = socket(AF_INET, SOCK_STREAM)
        tcp_client.connect((host_address , host_port))
    else:
        print("Command Error, quit.")
        break
```
## Result
### WebServer.py
```
you can test the web server by accessing: http://10.129.34.15:8899/hello.html
Wait for TCP clients...
Client (10.129.34.15: 6123) is coming...
Bye to Client (10.129.34.15: 6123)
Client (10.129.34.15: 6135) is coming...
Bye to Client (10.129.34.15: 6135)

C:\User\asus\Desktop\lab_solution\Web Server>python Client.py 8899
Hello, which document do you want to query?
I want to query: hello.html
```
### Client.py
```
Web server responded to your request:
HTTP/1.1 200 OK
Web server responded to your request:
<!DOCTYPE html>
<html>
<head>
<title>Hello World HTML</title>
</head>
<body>
<h1>Hello World</h1>
</body>
Web server responded to your request:
</html>

Do you want to cut this connection(y/n) :n
Anything else I can help you?
I want to query: index.html
Web server responded to your request:
HTTP/1.1 404 Not Found
Do you want to cut this connection(y/n) :y
Process finished with exit code 0
```
# Web代理服务器
## 目的
此任务是构建一个简单的 web 代理服务器。根据第4讲(Web 和 HTTP)中所学到的知识， web 代理服务器充当客户端和服务器，这意味着它具有 web 服务器和客户端的所有功能。它和 web 服务器之间最显着的区别是发送的请求报文
和响应报文都要通过 web 服务器传递。web 代理服务器在任何地方(大学,公司和住宅ISP)使用，以减少客户请求和流量的响应时间。
## 原理
web 代理服务器的原理基于 web 服务器。web 代理服务器从客户端接收 HTTP 请求报文，并从请求行中提取方法类型。
- 如果请求类型是 **GET**，从同一行获取URL并检查请求的对象是否存在于缓存中。否则，web 代理服务器会将客户端的请求转发给 web 服务器。然后，web 服务器将生成响应报文并将其传递给 web 代理服务器，web 代理服务器又将其发送到客户端并为将来的请求缓存副本。
- 如果请求类型是 **DELETE**，代理服务器会首先确认请求，如果对象存在缓存中，j只是从缓存中删除它并发送带有 Status-Code 200 的 HTTP 响应报文。否则，web 代理服务器发送带有 Status-Code 404 的 HTTP 响应报文。
- 如果请求类型是 **POST**, 处理过程比上述方法类型更容易，web 代理服务器只是以二进制格式将对象写入磁盘，然后发送带有 Status-Code 200 的 HTTP 响应报文(输入在实体行中上传)。如果方法是 PUT，则只需要在实体行中返回 true。
- 如果请求类型是 **HEAD**, web 代理服务器仅返回 HTTP 响应报文的报文首部行和状态行。

简化过程如下所示。
<p align="center"><img src ="images/f6.png"></p>

## 函数实现
基于上述原理，首先，创建一个支持 IPv4 的套接字并将其绑定在高于1024的端口上。web 代理服务器和 web 服务器非常类似，唯一区别是它是单线程的。

我在 StrProcess 类中添加了其他方法使 web 代理服务器获取对象或连接到 web 服务器的效率更高。

StrProcess 类源码：
```Python
class StrProcess(str):

    def __init__(self, str):
        """用字符型变量 str 初始该属性"""
        self.str = str

    def split_str(self):
        """实现分割操作"""
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
        """从 HTTP 请求行中提取请求方法"""
        return self.split_str()[0]

    def get_body(self):
        """从 HTTP 请求报文实体行中提取数据"""
        body_start = self.str.find('\r\n\r\n') + 4
        return self.str[body_start:]

    def get_referer(self):
        """从 HTTP 请求行中提取引用"""
        ref_pos = self.str.find('Referer: ') + 9
        ref_stop = self.str.find('\r\n', ref_pos+1)
        get_ref = self.str[ref_pos:ref_stop]
        get_ref_start = get_ref.find('9/') + 2
        get_ref_path = self.str[ref_pos+get_ref_start:ref_stop]
        return get_ref_path

    def get_path(self):
        """从 HTTP 请求请求行中提取URL"""
        original_path = self.split_str()[1]
        for i in range(len(original_path)):
            if original_path[i] == "/":
                original_path = original_path[i+1:]
                return original_path

    def change_name(self):
        """将所有特殊符号转换为 "-"。"""
        original_name = self.get_path()
        for i in range(len(original_name)):
            if original_name[i] == "/" or original_name[i] == "?" \
                    or original_name[i] == "=" or original_name[i] == "&" \
                    or original_name[i] == "%":
                original_name = original_name[:i] + "-" + original_name[i+1:]
        return original_name

    def get_hostname(self):
        """从URL中提取主机名"""
        whole_URL = self.get_path()
        for i in range(len(whole_URL)):
            if whole_URL[i] == "/":
                    host_name = whole_URL[:i]
                    return host_name
        return whole_URL
```
创建套接字后，web 代理服务器需要处理不同的 HTTP 请求类型和异常。在这部分中，文件处理应该以二进制格式使用，我们必须考虑对象类型(可以是.jpg，.svg，.ico等)。

处理 HTTP 请求源码：
```Python
def start_listen(tcp_socket, client_ip, client_port):

    # 1. 在连接套接字上从客户端接收请求报文。
    message = tcp_socket.recv(1024).decode()
    # 从strProc类创建新对象(handlestr)。
    handle_str = StrProcess(message)
    print("client is coming: {addr}:{port}".format(addr = client_ip, port = client_port))
    file_error = False
    global host
    try:
        command = handle_str.get_cmd_type()
        # 2. 从报文中提取所请求对象的路径(HTTP 首部行的第二部分)。
        filename = handle_str.change_name()
        # 3. 找到特定的方法类型并处理请求。
        if command == "DELETE" :
            # 删除缓存中存在的对象
            os.remove("./Cache/" + filename)
            tcp_socket.send(b"HTTP/1.1 200 OK\r\n\r\n")
            print("File is removed.")
        elif command == "GET" or command == "HEAD":
            print("Client want to {c} the {o}.".format(c=command, o=filename))
            # 检查请求的对象是否存在。
            f = open("./Cache/" + filename, "rb")
            file_content = f.readlines()
            f.close()
            if command == "GET":
                print("File in cache!")
                # 从磁盘中查找相应的文件(如果存在)。
                for i in range(0, len(file_content)):
                    tcp_socket.send(file_content[i])  # 发送 HTTP 响应报文。
            else:  # "HEAD" 方法。
                list_to_str = ""
                for i in range(0, len(file_content)):
                    list_to_str += file_content[i].decode()
                HTTP_header_end = list_to_str.find("\r\n\r\n")
                # 仅发送 HTTP 响应报文首部行。
                tcp_socket.send(list_to_str[:HTTP_header_end+4].encode())
        elif command == "PUT" or command == "POST":  # 只实现上传文件。
            f = open("./Cache/" + filename, "ab")
            f.write(b"HTTP/1.1 200 OK\r\n\r\n" + handle_str.get_body().encode())
            f.close()
            print("Update successfully!")
            tcp_socket.send(b"HTTP/1.1 200 OK\r\n\r\n")
            body_re = b"true" if command == "PUT" else handle_str.get_body().encode()
            tcp_socket.send(body_re)
        else:
            tcp_socket.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
    # 4. 如果缓存中不存在该文件，则处理异常。
    except (IOError, FileNotFoundError):
        if command == "GET":
            # 在代理服务器上创建套接字。
            c = socket(AF_INET, SOCK_STREAM)
            hostname = handle_str.get_hostname()
            file = handle_str.split_str()[1]
            print("The file isn't in the cache!")
            try:
                # 连接到端口80的套接字。
                c.connect((hostname, 80))
                host = hostname  # 记录真实的主机名。
                request = "GET " + "http:/" + file + " HTTP/1.1\r\n\r\n"
            except:
                try:
                    # 需要使用全局主机或引用主机名。
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
                # 将响应读入缓冲区。
                print("The proxy server have found the host.")
                # 在缓存中为请求的文件创建一个新文件。
                # 此外，将缓冲区中的响应发送到客户端套接字和缓存中的相应文件。
                writeFile = open("./Cache/" + filename, "wb")
                print("The proxy server is receiving data...")
                # 接受 HTTP 响应报文直到所有报文都被接收。
                while True:
                    data = c.recv(4096)
                    if not data:
                        break
                    sys.stdout.write(">")
                    # 将文件的内容发送到套接字。
                    tcp_socket.sendall(data)
                    writeFile.write(data)
                writeFile.close()
                sys.stdout.write("100%\n")
            c.close()
        elif command == "DELETE":
            tcp_socket.send(b"HTTP/1.1 204 Not Content\r\n\r\n")
    except (ConnectionResetError, TypeError):
        print("Bye to client: {addr}:{port}".format(addr = client_ip, port = client_port))
    # 关闭客户端的套接字。
    print("tcp socket closed\n")
    tcp_socket.close()
```
## Result
### Browser Test
<p align="center"><img src ="images/f7.jpg"></p>

### WebProxy.py
```
C:\Users\asus\Desktop\lab_solution\Web Proxy>python WebProxy.py 8899
Wait for TCP clients...
wait for request:
client is coming: 127.0.0.1:4596
Client want to GET the s-wd-facebook-rsv_bp-0-ch-tn-baidu-bar-rsv_spt-3-ie-utf-8-rsv_enter-1-oq-face-f-3-inputT-3356.
The file is not in the cache!
The proxy server have found the host.
The proxy server is receiving data...
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>100%
tcp socket closed
```
