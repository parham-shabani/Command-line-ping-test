import socket
import os
import sys
import struct
import time
import select
import binascii

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


def ping(host):
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        print(f"Could not resolve hostname: {host}")
        return

    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    icmp_socket.settimeout(2)

    packet = create_packet()

    try:
        icmp_socket.sendto(packet, (ip, 1))

        start_time = time.time()
        ready, _, _ = select.select([icmp_socket], [], [], 2)
        if ready:
            reply, address = icmp_socket.recvfrom(1024)
            end_time = time.time()
            elapsed_time = (end_time - start_time) * 1000
            print(f"Ping successful: time={elapsed_time:.2f}ms")
        else:
            print("Ping timed out")

    except socket.error as e:
        print(f"Error occurred: {e}")

    finally:    
        icmp_socket.close()

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 ping.py <host>")
        sys.exit(1)

    host = sys.argv[1]
    ping(host)

if __name__ == "__main__":
    main()