import socket
import math
import sys
import crcmod
import random
import threading

### Conections mode
SLOW_START = 1
CONGESTION_AVOIDANCE = 2
def fastrestransmit(received_ack):
    chunk = file_data[received_ack * chunk_size: (received_ack + 1) * chunk_size]
    crc_value = crc32_func(chunk)
    packet = str(received_ack).encode() + b"|" + str(crc_value).encode() + b":"+ chunk

    print(":: FT :: Sending part %d" % received_ack)
    sock.sendto(packet, address)    
    
mode = SLOW_START
crc32_func = crcmod.predefined.mkCrcFun('crc-32')

# Sender details
receiver_ip = "127.0.0.1"  # Receiver's IP address
receiver_port = 34754     # Receiver's port number

# Test features
LoseTest = False
CoruptTest = False

# Code start =============================================================================== #

filename = sys.argv[1]
if sys.argv[2] != "-local":
    receiver_ip = sys.argv[2]

if len(sys.argv) > 3:
    if "-losePKG:" in sys.argv[3]:
        LoseTest = True
        LosePKG = int(sys.argv[3].replace("-losePKG:",""))
        print("TEST ACTIVE: Will lose pkg -> " + str(LosePKG))
    if "-coruptPKG:" in sys.argv[3]:
        CoruptTest = True
        CoruptPKG = int(sys.argv[3].replace("-coruptPKG:",""))
        print("TEST ACTIVE: Will corrupt pkg -> " + str(CoruptPKG))

print("#<<<<<< Sending: " + filename + " to: " + receiver_ip + " >>>>>>#")

# Read the file
with open(filename, "rb") as file:
    file_data = file.read()

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set up connection -------------------------------------------------------------------------- #
print("Sending SYNC request to: %s" % receiver_ip)
sock.sendto(b"SYN", (receiver_ip, receiver_port))

syn_ack, address = sock.recvfrom(1024)

if syn_ack == b"SYN-ACK":
    print("Sync ok")

sock.sendto(filename.encode(), (receiver_ip, receiver_port))

start_ack, address = sock.recvfrom(1024)

if start_ack == b"AGREED":
    print("Agreed ACK received")

    sock.settimeout(15)

# Transmition start ------------------------------------------------------------------------- #
    print("Sending Init transfer ACK")
    sock.sendto(b"ACK", address)
    
    # Send the file data
    seq_num = 0
    chunk_size = 300
    total_chunks = (len(file_data) // chunk_size) + 1
    print(total_chunks)

    fastRestransmitCount=0
    lastack = -1 
    cwnd = 1
    cwndlimit = 32
    cwnd_treshold = 8    # <-Trasnmition window treshhold to congestion avvoidance change
    sent = 0             # <-Trasnmition control
    waitingAcks=[]       # <-List of expected acks
    while seq_num < total_chunks:
        
        # ----------------------------------------------------------------------------------------- #
        if mode == SLOW_START:
            # Send packages
            while sent != cwnd and seq_num <= total_chunks:
            
                chunk = file_data[seq_num * chunk_size: (seq_num + 1) * chunk_size]
                crc_value = crc32_func(chunk)
                packet = str(seq_num).encode() + b"|" + str(crc_value).encode() + b":"+ chunk

                # print(len(packet))
                print("Sending part %d" % seq_num)
                if LoseTest:
                    if seq_num != LosePKG:
                        sock.sendto(packet, address)
                elif CoruptTest:
                    if seq_num != CoruptPKG:
                        sock.sendto(packet, address)
                    else:
                        str_var = list(str(chunk))
                        random.shuffle(str_var)
                        packet = str(seq_num).encode() + b"|" + str(crc_value).encode() + b":"+ "".join(str_var).encode()
                        sock.sendto(packet, address) 
                else:
                   sock.sendto(packet, address) 
                waitingAcks.append(seq_num)
                seq_num+=1
                sent+=1
            sent = 0

            # Wait for ACKs
            while len(waitingAcks) != 0:
                try:
                    received_ack, _ = sock.recvfrom(1024)
                except socket.timeout:
                    print("Timeout - Changed to Slow Start")
                    mode = SLOW_START
                    waitingAcks = []
                    cwnd = 1
                    seq_num = lastack
                    break

                ack_seq_num = int(received_ack.decode())
                print("Received ACK num: %d" % ack_seq_num)

                # Fast retrasnsmit Action ----------- #
                if ack_seq_num == lastack:
                    fastRestransmitCount+=1
                    if fastRestransmitCount == 3:
                        fastrestransmit(ack_seq_num)
                        fastRestransmitCount = 0
                        seq_num = ack_seq_num + 1
                        cwnd = int(math.ceil(cwnd/2))
                        mode = CONGESTION_AVOIDANCE
                # ----------------------------------- #

                if cwnd <= cwnd_treshold and mode !=CONGESTION_AVOIDANCE:
                    if cwnd < cwndlimit:
                        cwnd+=1
                else:
                    mode = CONGESTION_AVOIDANCE
                    #print("[*] Changed to Congestion Avoidance [*]")

                lastack = ack_seq_num
                if ack_seq_num > max(waitingAcks):
                    waitingAcks = []
                    seq_num = ack_seq_num
                if ack_seq_num-1 in waitingAcks:
                    waitingAcks.remove(ack_seq_num-1)

        # ----------------------------------------------------------------------------------------- #
        if mode == CONGESTION_AVOIDANCE:
            # Send packages
            while sent != cwnd and seq_num <= total_chunks:
                 
                chunk = file_data[seq_num * chunk_size: (seq_num + 1) * chunk_size]
                crc_value = crc32_func(chunk)
                packet = str(seq_num).encode() + b"|" + str(crc_value).encode() + b":"+ chunk

                print("Sending part %d" % seq_num)
                if LoseTest:
                    if seq_num != LosePKG:
                        sock.sendto(packet, address)
                elif CoruptTest:
                    if seq_num != CoruptPKG:
                        sock.sendto(packet, address)
                    else:
                        str_var = list(str(chunk))
                        random.shuffle(str_var)
                        packet = str(seq_num).encode() + b"|" + str(crc_value).encode() + b":"+ "".join(str_var).encode()
                        sock.sendto(packet, address)
                else:
                   sock.sendto(packet, address) 
                waitingAcks.append(seq_num)
                seq_num+=1
                sent+=1
            sent = 0

            # Wait for ACKs
            while len(waitingAcks) != 0:
                try:
                    received_ack, _ = sock.recvfrom(1024)
                except socket.timeout:
                    print("Timeout - Changed to Slow Start")
                    mode = SLOW_START
                    waitingAcks = []
                    cwnd = 0
                    seq_num = lastack
                    break

                ack_seq_num = int(received_ack.decode())
                print("Received ACK num: %d" % ack_seq_num)
                
                # Fast retransmit Action ----------- #
                if ack_seq_num == lastack:
                    fastRestransmitCount+=1
                    if fastRestransmitCount == 3:
                        fastrestransmit(ack_seq_num)
                        fastRestransmitCount = 0
                        seq_num = ack_seq_num + 1
                        cwnd = int(math.ceil(cwnd/2))
                # ----------------------------------- #

                lastack = ack_seq_num
                if ack_seq_num > max(waitingAcks):
                    waitingAcks = []
                    seq_num = ack_seq_num
                if ack_seq_num-1 in waitingAcks:
                    waitingAcks.remove(ack_seq_num-1)
            if cwnd < cwndlimit:
                cwnd+=1

            
crc_value = crc32_func(chunk)
packet = str(-1).encode() + b"|" + str(crc_value).encode() + b":"+ chunk
sock.sendto(packet, address)
# Close the socket
sock.close()
