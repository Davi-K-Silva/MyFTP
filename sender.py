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
with open("testfile.txt", "rb") as file:
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

    cwnd = 1
    cwnd_treshold = 16
    sent = 0
    waitingAcks=[]
    while seq_num < total_chunks:

        if mode == SLOW_START:
            # Send packages
            while sent != cwnd:
                chunk = file_data[seq_num * chunk_size: (seq_num + 1) * chunk_size]
                packet = str(seq_num).encode() + b":" + chunk
                print("Sending part %d" % seq_num)
                sock.sendto(packet, address)
                waitingAcks.append(seq_num)
                seq_num+=1
                sent+=1
            sent = 0

            # Wait for ACKs
            while len(waitingAcks) != 0:
                received_ack, _ = sock.recvfrom(1024)
                ack_seq_num = int(received_ack.decode())
                print("Received ACK num: %d" % ack_seq_num)
                if cwnd <= cwnd_treshold:
                    cwnd+=1
                waitingAcks.remove(ack_seq_num-1)
            
        

packet = str(-1).encode() + b":" + chunk
sock.sendto(packet, address)
# Close the socket
sock.close()
