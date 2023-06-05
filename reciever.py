import socket

# Receiver details
receiver_ip = "127.0.0.1"  # Receiver's IP address
receiver_port = 34754     # Receiver's port number

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket
sock.bind((receiver_ip, receiver_port))

# Connection setup
syn_packet, address = sock.recvfrom(1024)

if syn_packet == b"SYN":
    print("SYNC  request received")

    print("Sendind SYN-ACK")
    sock.sendto(b"SYN-ACK", address)
    ack, _ = sock.recvfrom(1024)

    if ack == b"ACK":
        print("init Transfer ACK received")
        # Receive the file data
        expected_seq_num = 0
        file_data = b""
        received_packets = []

        while True:
            packet, address = sock.recvfrom(1024)
            seq_num, _, chunk = packet.partition(b":")
            seq_num = int(seq_num.decode())

            if seq_num == -1:
                break
            
            if seq_num == expected_seq_num and seq_num not in received_packets:
                received_packets.append(seq_num)
                file_data += chunk
                print("received %d" % seq_num)
                #print(str(file_data))
                ack_packet = str(seq_num+1).encode()
                sock.sendto(ack_packet, address)
                expected_seq_num += 1
            else:
                ack_packet = str(expected_seq_num).encode()
                sock.sendto(ack_packet, address)

        # Write the file
        with open("received_file.txt", "wb") as file:
            file.write(file_data)

# Close the socket
sock.close()