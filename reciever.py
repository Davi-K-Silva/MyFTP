import socket
import crcmod
import sys
from socket import gethostbyname,gethostname

def checkCRC(packet):
    crc32_func = crcmod.predefined.mkCrcFun('crc-32')
    seq_num, _, chunkFirst = packet.partition(b"|")
    crc_packet, _ , chunk = chunkFirst.partition(b":")
    if str(crc32_func(chunk)).encode() == crc_packet:
        return True
    return False
    
if len(sys.argv) > 1:
    if sys.argv[1] == "-local":
        receiver_ip = "127.0.0.1"  # Receiver's IP address
else:
    receiver_ip = gethostbyname(gethostname())

receiver_port = 34754     # Receiver's port number

print("#<<<<<< Im at: " + receiver_ip + " on PORT: " + str(receiver_port)+ " >>>>>>#")
# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket
sock.bind(('', receiver_port))

# Connection setup
syn_packet, address = sock.recvfrom(1024)

if syn_packet == b"SYN":
    print("SYNC request received")

    print("Sendind SYN-ACK")
    sock.sendto(b"SYN-ACK", address)
    
    filename, _ = sock.recvfrom(1024)
    print("Received filename: " + filename.decode() + "\nSending AGREE and waiting init ack")
    sock.sendto(b"AGREED", address)
   
    ack, _ = sock.recvfrom(1024)

    if ack == b"ACK":
        print("init Transfer ACK received")
        # Receive the file data
        expected_seq_num = 0
        file_data = []
        received_packets = []
        lostpkg = False

        while True:
            packet, address = sock.recvfrom(1024)
            if checkCRC(packet):
                seq_num, _, chunkFirst = packet.partition(b"|")
                seq_num = int(seq_num.decode())
                crc_value, _ , chunk = chunkFirst.partition(b":")

                if seq_num == -1:
                    break
                
                if seq_num == expected_seq_num and seq_num not in received_packets:
                    received_packets.append(seq_num)
                    file_data.append((seq_num,chunk))
                    print("received %d" % seq_num)
    
                    if lostpkg:
                        expected_seq_num = max(received_packets)+1
                        lostpkg = False
                    else:
                        expected_seq_num += 1
                    ack_packet = str(expected_seq_num).encode()
                    sock.sendto(ack_packet, address)
                else:
                    lostpkg= True
                    received_packets.append(seq_num)
                    file_data.append((seq_num,chunk))
                    ack_packet = str(expected_seq_num).encode()
                    sock.sendto(ack_packet, address)
            else:
                lostpkg= True
                print("Received Corrupted pkg - discarding")
                ack_packet = str(expected_seq_num).encode()
                sock.sendto(ack_packet, address)


        # Write the file
        final_file = b""
        expected = 0
        file_data.sort(key=lambda x: x[0])
        for seq in file_data:
            _ , part = seq
            final_file += part            

        with open(filename, "wb") as file:
            file.write(final_file)

# Close the socket
sock.close()