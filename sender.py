import socket

### Conections mode
SLOW_START = 1
CONGESTION_AVOIDANCE = 2
FAST_RETRANSMIT = 3

mode = SLOW_START

# Sender details
receiver_ip = "127.0.0.1"  # Receiver's IP address
receiver_port = 34754     # Receiver's port number


# Read the file
with open("bible.txt", "rb") as file:
    file_data = file.read()

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set up connection
print("Sending SYNC request to: %s" % receiver_ip)
sock.sendto(b"SYN", (receiver_ip, receiver_port))

syn_ack, address = sock.recvfrom(1024)

if syn_ack == b"SYN-ACK":
    print("ACK received")

    print("Sending Init transfer ACK")
    sock.sendto(b"ACK", address)
    
    # Send the file data
    seq_num = 0
    chunk_size = 300
    total_chunks = (len(file_data) // chunk_size) + 1
    print(total_chunks)


    n2send = 1
    send = 0
    while seq_num < total_chunks:

        # if mode == SLOW_START:
        #     while send != n2send
            

        chunk = file_data[seq_num * chunk_size: (seq_num + 1) * chunk_size]
        packet = str(seq_num).encode() + b":" + chunk
        print("Sending part %d" % seq_num)
        sock.sendto(packet, address)

    
        # Wait for ACK
        received_ack, _ = sock.recvfrom(1024)
        ack_seq_num = int(received_ack.decode())
        print("Received ACK num: %d" % ack_seq_num)

        if ack_seq_num == seq_num + 1:
            seq_num += 1

packet = str(-1).encode() + b":" + chunk
sock.sendto(packet, address)
# Close the socket
sock.close()
