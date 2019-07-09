#!/usr/bin/env python3
#-*-coding:utf-8-*-
# @Time    : 2018/11/25 7:50
# @Author  : Hephaest

from socket import *
import socket
import os
import sys
import struct
import time
import select

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages.
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages.
MAX_HOP = 30
TIMES = 3

def checksum(string):
    """Fetch string and calculate the checksum.

    This function is copied from sample code file.

    Args:
        :param string: A string of the time in seconds since the epoch.

    Returns:
        :return: The value of checksum (integer type).
    """
    csum = 0
    count_to = (len(string) // 2) * 2
    count = 0
    while count < count_to:
        thisVal = string[count + 1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2
    if count_to < len(string):
        csum = csum + string[len(string) - 1]
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receive_one_trace(icmp_socket, send_time, timeout):
    """The socket waits for a reply and calculate latency for each node.

        This function will measure and report different packet loss.

        Args:
            :param icmp_socket: the socket which is created from do_three_trace function.
            :param timeout: configurable timeout, set using an optional argument.
            :param send_time: the time when ICMP packet is sent.

        Returns:
        :return: the IP address of the current node.

        Raises:
            TimeoutError: An error occurred when a packet cannot be received within
                          a given time range.
        """
    print_str = ""
    retr_addr = ""
    try:
        # 1. Wait for the socket to receive a reply.
        start_time = time.time()
        wait_for_data = select.select([icmp_socket], [], [], timeout)
        end_time = time.time()
        if end_time == start_time:
            #wait 1 ms
            time.sleep(0.001)
        # 2. Once received, record the time.
        data_received = time.time()
        rec_packet, retr_addr = icmp_socket.recvfrom(1024)
        icmp_header = rec_packet[20: 28]
        # 3. Unpack the packet header for useful information.
        type, code, checksum, id, sequence = struct.unpack("!bbHHh", icmp_header)
        # 4. Check whether packet loss or not by its type and code.
        if type == 0 or type == 11:
            # When TTL reaches 0 but it haven't reach the destination.
            delay_time = int((data_received - send_time) * 1000)
            print_str = str(delay_time) + " ms"
        elif type == 3 and code == 0:
            # Network unreachable error.
            print_str = "Network unreachable"
        elif type == 3 and code == 1:
            # Host unreachable error.
            print_str = "Host unreachable"
    except TimeoutError :
        print_str = "*   "  # timeout.
    finally:
        sys.stdout.write("{0: >18}".format(print_str))
    # return IP address of the current node.
    # If request timeout, just return the string.
    try:
        retre_ip = retr_addr[0]
    except IndexError:
        retre_ip = "Request timeout"
    finally:
        return retre_ip


def send_one_trace(icmp_socket, dest_addr, port_id, sequence):
    """Build, pack and send the ICMP packet using socket.

    Args:
        :param icmp_socket: the socket which is created from do_three_trace function.
        :param dest_addr: the IP address of the current node.
        :param port_id: current process id.
        :param sequence: the nth times of the current node latency measurement.

    Returns:
        :return: the time when packet is sent.
    """
    # 1. Build ICMP header, start with a 0 checksum.
    icmp_header = struct.pack("!bbHHh", ICMP_ECHO_REQUEST, 0, 0, port_id, sequence)
    payload_data = struct.pack("!f", time.time())
    # 2. Checksum ICMP packet using given function.
    packet_checksum = checksum(icmp_header + payload_data)
    # 3. Insert checksum into packet.
    icmp_header = struct.pack("!bbHHh", ICMP_ECHO_REQUEST, 0, packet_checksum, port_id, sequence)
    packet = icmp_header + payload_data
    # 4. Send packet using socket.
    icmp_socket.sendto(packet, (dest_addr, 1))
    # 5. Record time of sending.
    send_time = time.time()
    return send_time


def do_three_trace(dest_addr, ttl, sequence, time_out):
    """Create ICMP socket, send it and receive IP address of the current node.

    After extracting the current node IP address from receiveOneTrace function,
    we need to close the socket in order to cut the connection.

    Args:
        :param dest_addr: the IP address of the current node.
        :param ttl: Time To Live value.
        :param sequence: the nth times of the current node latency measurement.
        :param time_out: configurable timeout, set using an optional argument.

    Returns:
        :return: the IP address of the current node or a string ("Request timeout").
    """
    port_id = os.getpid()
    record_addr =""
    record = False
    for i in range(TIMES):
        # 1 is socket module constant associated with protocol ICMP.
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, 1)  # icmp.
        client_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))  # stop after ttl = 0
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, time_out)
        # 2. Call send_one_trace function.
        send_time = send_one_trace(client_socket, dest_addr, port_id, sequence)
        # 3. Call receive_one_trace function.
        route_addr = receive_one_trace(client_socket, send_time, time_out)
        if route_addr != "Request timeout" :
            record = True
            record_addr = route_addr
        client_socket.close()
    # During [TIMES] times measurements, once we get real IP address then record it.
    # Else, return "Request timeout".
    if record is True:
        return record_addr
    else:
        return route_addr


def trace_route(host, timeout=2):
    """Print the header and each measurement result in given format.

    Args:
        :param host: destination hostname or destination IP address.
        :param timeout: configurable timeout, set using an optional argument.
    """
    # 1. Look up hostname, resolving it to an IP address.
    ip_addr = socket.gethostbyname(host)
    ttl = 1
    print("Over a maximum of {max_hop} hops:\n".format(max_hop = MAX_HOP))
    print("Tracing route to " + host + " [{hostIP}]:".format(hostIP = ip_addr))
    for i in range(MAX_HOP):  # i is nth of hop.
        sys.stdout.write("{0: >3}".format(str(ttl)+"\t"))
        cur_addr = do_three_trace(ip_addr, ttl, i, timeout)
        try:
            sys.stdout.write("{0:<}".format("  " + socket.gethostbyaddr(cur_addr)[0]
                                        + " [" + cur_addr + "]" + "\n"))
        except (socket.herror, socket.gaierror):
            sys.stdout.write("{0:<}".format("  " + cur_addr + "\n"))
        if cur_addr == ip_addr :
            break
        ttl += 1
    sys.stdout.write("\nTrace complete.\n\n")


def start_trace(*fuzzy_search_list):
    """Enter the tracert command, start test and catch the exceptions.

    This function simulates tracert, an executable command on the
    Windows operating system. It will catch a wrong command before a test
    and print a warning.

    Args:
        :param fuzzy_search_list: Ignore case to find the correct command.

    Raises:
        socket.gaierror: The destination host name could not be resolved.
        ValueError: the parameter for option "-w" is wrong.
    """
    startflag = True
    while startflag:
        command = input(os.getcwd() + ">" + os.path.basename(sys.argv[0]) + ">").split()
        cmdLen = len(command)
        if cmdLen == 0:
             # Okay, pass.
             continue
        elif cmdLen == 1:
            if command[0] == "exit":
             startflag = False
            else:
             print("Command error.")
        elif cmdLen == 2:
            if command[0] in fuzzy_search_list:
                try:
                    trace_route(command[1])
                except socket.gaierror:
                    print("The destination host name " + command[1] + " could not be resolved.")
            else:
                print("Command error.")
        elif cmdLen == 4 :
            if command[0] in fuzzy_search_list:
                if command[1] == "-w":
                    try:
                        trace_route(command[3], int(command[2]))
                    except ValueError:
                        print("Bad value for option -w, ",end = "")
                        print("valid range is from 1 to 4294967295.")
                    except socket.gaierror:
                        print("The destination host name " + command[1] + " could not be resolved.")
                else:
                    print("Command error.")
            else:
                print("Command error.")
        else:
            print("Command error.")
        # Tricky tip: leave the cursor at the end.
        time.sleep(0.3)


fuzzy_search = ["tracert", "TRACERT"]  # Start here.
start_trace(*fuzzy_search)