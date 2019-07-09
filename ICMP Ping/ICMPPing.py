#!/usr/bin/env python3
#-*-coding:utf-8-*-
# @Time    : 2018/11/24 22:48
# @Author  : Hephaest

import socket
import os
import sys
import struct
import time
import select

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages.
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages.


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
        this_val = string[count + 1] * 256 + string[count]
        csum = csum + this_val
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


def ping_statistics(list):
    """Find the minimum, maximum and average latency.

    Args:
        :param list: the list of delay time where packet is received successfully.

    Returns:
        :return: minimum, maximum and average latency (integer type).
    """
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


def receive_one_ping(icmp_socket, port_id, timeout, send_time):
    """The socket waits for a reply and calculate latency.

    This function will measure and report different packet loss.

    Args:
        :param icmp_socket: the socket which is created from doOnePing function.
        :param port_id: current process id.
        :param timeout: configurable timeout, set using an optional argument.
        :param send_time: the time when ICMP packet is sent.

    Returns:
        :return: 1 (if Host unreachable error).
                 0 (if Network unreachable error).
                 byte size, latency and ttl (for successful reply).

    Raises:
        TimeoutError: An error occurred when a packet cannot be received within
                      a given time range.
    """
    while True:
        # 1. Wait for the socket to receive a reply.
        wait_for_data = select.select([icmp_socket], [], [], timeout)
        # 2. Once received, record the time.
        data_received = time.time()
        rec_packet, addr = icmp_socket.recvfrom(1024)
        ip_header = rec_packet[8: 12]
        icmp_header = rec_packet[20: 28]
        payload_size = struct.calcsize("!f")
        # 3. Unpack the packet header for useful information.
        type, code, checksum, id, sequence = struct.unpack("!bbHHh", icmp_header)
        # 4. Check that the ID matches between the request and reply.
        if type == 0 and id == port_id:  # type should be 0.
            ttl = struct.unpack("!b", ip_header[0:1])[0]
            delay_time = data_received - send_time
        # 5. Return byte size, latency and TTL.
            return payload_size * 8, delay_time, ttl
        elif type == 3 and code == 0:
            return 0  # Network unreachable error.
        elif type == 3 and code == 1:
            return 1  # Host unreachable error.


def send_one_ping(icmp_socket, dest_addr, port_id, sequence):
    """Build, pack and send the ICMP packet using socket.

    Args:
        :param icmp_socket: the socket which is created from doOnePing function.
        :param dest_addr: the IP address of the destination host.
        :param port_id: current process id.
        :param sequence: the nth times of the latency test.

    Returns:
        :return: the time when packet is sent.
    """
    # 1. Build ICMP header, start with a 0 checksum.
    icmp_header = struct.pack("!bbHHh", ICMP_ECHO_REQUEST, 0, 0, port_id, sequence)
    # 2. Checksum ICMP packet using given function.
    payload_data = struct.pack("!f", time.time())
    packet_checksum = checksum(icmp_header + payload_data)
    # 3. Insert checksum into packet.
    icmp_header = struct.pack("!bbHHh", ICMP_ECHO_REQUEST, 0, packet_checksum, port_id, sequence)
    packet = icmp_header + payload_data
    # 4. Send packet using socket.
    icmp_socket.sendto(packet, (dest_addr, 80))
    # 5. Record time of sending.
    send_time = time.time()
    return send_time


def do_one_ping(dest_addr, timeout, sequence):
    """Create ICMP socket and then send, receive packets of the same size.

    After getting the delay time from receiveOnePing function, we need to close
    the socket in order to cut the connection.

    Args:
        :param dest_addr: the IP address of the destination host.
        :param timeout: configurable timeout, set using an optional argument.
        :param sequence: the n times of ping.

    Returns:
        :return: the delay time between the socket send and receive a packet.
    """
    port_id = os.getpid()  # get current process id.
    # 1. Create ICMP socket
    # 1 is socket module constant associated with protocol ICMP.
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, 1)
    # Set the timeout value for the socket.
    icmp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeout)
    # 2. Call sendOnePing function.
    send_time = send_one_ping(icmp_socket, dest_addr, port_id, sequence)
    # 3. Call receiveOnePing function.
    receive_data = receive_one_ping(icmp_socket, port_id, timeout, send_time)
    # 4. Close ICMP socket.
    icmp_socket.close()
    # 5. Return delay information.
    return receive_data


def ping(host, count_num="4", time_out="1"):
    """Print the result to the console.

    This function will print the IP address of the host, byte size, latency
    and TTL of a packet or handle an exception after each ping.

    Args:
        :param host: The website or IP address that we want to test latency.
        :param count_num: the total number of the network delay test.
        :param timeout: configurable timeout, set using an optional argument.
    """
    # 1. Look up hostname, resolving it to an IP address.
    ip_addr = socket.gethostbyname(host)
    successful_list = list()
    lost = 0
    error = 0
    bytes = 32
    count = int(count_num)
    timeout = int(time_out)
    timeout_start = 0
    head = False
    timedout_mark = False
    for i in range(count):  # i is value of sequence.
        # Print header.
        if head is False:
            if host == ip_addr:
                print("Pinging {ipAddr} with {bytes} of data:"
                      .format(ipAddr = ip_addr, bytes = bytes))
            else:
                print("Pinging {hostName} [{ipAddr}] with {bytes} of data:"
                      .format(hostName = host, ipAddr = ip_addr, bytes = bytes))
            head = True
        try:
            # 2. Call doOnePing function.
            ping_delay = do_one_ping(ip_addr, timeout, i)
            # 3. Print out the returned delay information.
            if ping_delay == 0 or ping_delay == 1:
                # To get my laptop's IP address.
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
                # If a packet can be received successfully,
                # the list could append this delay time.
                successful_list.append(delay_time)
                # if delay_time < 1m, then we will get 0 ms.
                if delay_time == 0:
                    print("bytes = {bytes} time < 1ms TTL = {ttl}."
                          .format(bytes = bytes, ttl = ttl))
                else:
                    print("bytes = {bytes} time = {delayTime}ms TTL = {ttl}."
                          .format(bytes = bytes, delayTime = delay_time, ttl = ttl))
        except TimeoutError:  # timeout type
            lost += 1
            print("Request timed out.")
            # If it's not always a timeout case,
            # we might need to calculate the maximum latency.
            if timedout_mark is False:
                timedout_mark = True
        time.sleep(1)  # Every second.
    #  4. Continue this process until stopped.
    print("\nPing statistics for {ipAddr}:\n".format(ipAddr = ip_addr), end = "")
    print("\tPacket: Sent = {c}, Received = {receiveAmt}, lost = {lostAmt} ({lostPercent}% loss)."
        .format(c = count, receiveAmt = count - lost, lostAmt = lost, lostPercent = int((lost / 4) * 100)))
    if lost < count and error <= 0:
        sortResult = ping_statistics(successful_list)
        mini_delay, max_delay, avg_delay = sortResult[0], sortResult[1], sortResult[2]
        max_delay = max_delay if timedout_mark is False else timeout*1000
        print("Approximate round trip times in milli - seconds:\n", end = "")
        print("\tMinimum = {mini}ms, Maximum = {max}ms, Average = {ave}ms.\n"
            .format(mini = mini_delay, max = max_delay, ave = avg_delay))


def start_ping(*fuzzy_search_list):
    """ Enter the ping command, start test and catch the exceptions.

    This function simulates ping, an executable command on the
    Windows operating system. It will catch a wrong command before a test
    and print a warning.
    Args:
        :param fuzzy_search_list: Ignore case to find the correct command.

    Raises:
        socket.gaierror: Hostname might be wrong.
        IndexError: Optional argument is empty.
        ValueError: the parameter for option is wrong.
    """
    start_flag = True
    while start_flag:
        command = input(os.getcwd() + ">" +
                        os.path.basename(sys.argv[0]) + ">").split()
        cmd_len = len(command)
        if cmd_len == 0:
            # Okay, pass.
            continue
        elif cmd_len == 1:
            if command[0] == "exit":
                start_flag = False
            else:
                print("Command error.")
        elif cmd_len == 2:
            if command[0] in fuzzy_search_list:
                try:
                    # Default measurement count and timeout.
                    ping(command[1])
                except socket.gaierror:
                    print("Ping Request Could not Find Host. " +
                          "Please Check the Name and Try again.")
        elif cmd_len in range(3,5):
            if command[0] in fuzzy_search_list:
                try:
                    if command[2] == "-n":
                        # Default timeout and configurable measurement count.
                        ping(command[1], command[3])
                    elif command[2] == "-w":
                        # Default measurement count and configurable timeout.
                        ping(command[1], "4", command[5])
                    else:
                        print("Option {op} is incorrect.".format(op = command[2]))
                except IndexError:
                    print("Must set a value for option {op}.".format(op = command[2]))
                except ValueError:
                    print("Bad value for option {op}, ".format(op = command[2]), end="")
                    print("valid range is from 1 to 4294967295.")
                except socket.gaierror:
                    print("Ping Request Could not Find Host. " +
                          "Please Check the Name and Try again.")
            else:
                print("Command error.")
        elif cmd_len in range(5,7):
            if command[0] in fuzzy_search_list:
                # Configurable measurement count and timeout.
                if command[2] == "-n" and command[4] == "-w":
                    try:
                        ping(command[1], command[3], command[5])
                    except IndexError:
                        print("Must set a value for option ",command[4],".")
                    except ValueError:
                        op = command[2] if command[3].isdigit() is False else command[5]
                        print(
                            "Bad value for option {op}, ".format(op = op)+
                            "valid range is from 1 to 4294967295.")
                    except socket.gaierror:
                        print("Ping Request Could not Find Host. " +
                              "Please Check the Name and Try again.")
                else:
                    print("Command error.")
            else:
                print("Command error.")
        else:
            print("Command error.")
        # Tricky tip: leave the cursor at the end.
        time.sleep(0.3)


fuzzy_search = ["ping", "PING"]  # Start here.
start_ping(*fuzzy_search)