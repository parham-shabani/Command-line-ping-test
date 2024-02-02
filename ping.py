import socket
import os
import sys
import struct
import time
import select

ICMP_ECHO_REQUEST = 8

def checksum(data):
    if len(data) % 2 != 0:
        data += b'\x00'
    checksum = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i+1]
        checksum += word
        checksum = (checksum & 0xffff) + (checksum >> 16)
    checksum = ~checksum & 0xffff
    return checksum

def create_packet():
    identifier = os.getpid() & 0xffff
    payload = struct.pack('d', time.time())
    header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, 0, identifier, 1)
    checksum_val = checksum(header + payload)
    header_with_checksum = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, checksum_val, identifier, 1)
    packet = header_with_checksum + payload
    return packet

def parse_reply(reply):
    header = reply[20:28]
    rtt = struct.unpack('d', header)[0]
    return rtt

def ping(host, num_requests):
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        print(f"Could not resolve hostname: {host}")
        return

    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    icmp_socket.settimeout(2)

    packet = create_packet()

    total_rtt = 0
    lost_packets = 0
    min_ping = float('inf')
    max_ping = float('-inf')

    try:
        for _ in range(num_requests):
            icmp_socket.sendto(packet, (ip, 1))

            start_time = time.time()
            ready, _, _ = select.select([icmp_socket], [], [], 2)
            if ready:
                reply, address = icmp_socket.recvfrom(1024)
                rtt = parse_reply(reply)
                end_time = time.time()
                elapsed_time = (end_time - start_time) * 1000
                total_rtt += elapsed_time
                min_ping = min(min_ping, elapsed_time)
                max_ping = max(max_ping, elapsed_time)
                print(f"Ping successful: time={elapsed_time:.2f}ms")
            else:
                print("Ping timed out")
                lost_packets += 1

    except socket.error as e:
        print(f"Error occurred: {e}")

    finally:
        icmp_socket.close()


    if num_requests > 0:
        avg_ping = total_rtt / num_requests
    else :
        avg_ping = 0

    if num_requests > 0:
        packet_loss_percentage = (lost_packets / num_requests) * 100
    else:
        packet_loss_percentage = 0

    print(f"\nPing statistics for {host}:")
    print(f"    Packets: Sent = {num_requests}, Received = {num_requests - lost_packets}, Lost = {lost_packets} ({packet_loss_percentage:.2f}% loss)")
    if (packet_loss_percentage != 100):
        print(f"Approximate round trip times in milliseconds:")
        print(f"    Minimum = {min_ping:.2f}ms, Maximum = {max_ping:.2f}ms, Average = {avg_ping:.2f}ms\n")

    print(f"IP: {ip}")    


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 ping.py <domain or host> <num_requests>")
        sys.exit(1)

    host = sys.argv[1]
    num_requests = int(sys.argv[2])
    ping(host, num_requests)

if __name__ == "__main__":
    main()