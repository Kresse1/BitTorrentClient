import struct
import socket
import random
import torrent_file
import secrets
import string

# UDP Tracker Protocol Constants
PROTOCOL_ID = 0x41727101980
ACTION_CONNECT = 0
ACTION_ANNOUNCE = 1
EVENT_NONE = 0
EVENT_COMPLETED = 1
EVENT_STARTED = 2
EVENT_STOPPED = 3

# Packet sizes
CONNECT_REQUEST_SIZE = 16
CONNECT_RESPONSE_SIZE = 16
ANNOUNCE_RESPONSE_HEADER_SIZE = 20
PEER_SIZE = 6
DEFAULT_BUFFER_SIZE = 1024

# Defaults
DEFAULT_PORT = 6881
DEFAULT_NUM_WANT = -1
DEFAULT_TIMEOUT = 5.0

def build_connect_request():
    """
    Builds a packet which is used to Connect to a UDP tracker.

    Returns:
        tuple: (packet: bytes, transaction_id: int)
    
    """
    transaction_id = random.getrandbits(32)
    packet = struct.pack('>QII', PROTOCOL_ID, ACTION_CONNECT, transaction_id)    
    return packet, transaction_id


def send_request(tracker_host, tracker_port, packet):
    """
    Sends a packet to the host.
    Parameter: 
        tracker_host(string)
        tracker_port(int)
        packet(bytes)
    Returns:
        tuple: response(byte), addr(string)
    """   
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(DEFAULT_TIMEOUT)

    try:
        sock.sendto(packet, (tracker_host, tracker_port))
        response, addr = sock.recvfrom(DEFAULT_BUFFER_SIZE)
        return response, addr
            
    except socket.gaierror as e:
        raise(f"Host name is invalid. Given host name is {tracker_host}. Check the torrent info.")
        
    except socket.timeout as e:
        raise(f"Timeout while waiting on tracker {tracker_host}. Maybe try again?")
    except socket.error as e:
        raise Exception(f"Socket error: {e}")
    finally:
        sock.close()
    

def parse_connect_response(data, expected_trans_id):
    """
    Parses the response of a connect request. Asserts if transaction_id is correct.
    Parameter: data(byte), expected_trans_id(int)
    Returns:
        tuple: action(int), trans_id(int), con_id(int)
    """
    unpack = struct.unpack(">IIQ", data) # Q= 64 bit I = 32 bit , response is 32-bit 32-bit and 64-bi
    action = unpack[0]
    trans_id = unpack[1]
    con_id = unpack[2]

    assert(trans_id == expected_trans_id), f"Assertion failed. trans_id = {trans_id}, expected = {expected_trans_id}"
    
    return (action, trans_id, con_id)

def build_announce_request(con_id, info_hash, peer_id, downloaded, left, uploaded):
    """
    Build a packet for an announce request. 
    Parameter:
        con_id(int): the Connection ID
        info_hash(string): SHA1-Hash des bencodeten info-Dictionarys
        peer_id(string)
        downloaded()
        left()
        uploaded()
    Returns:
        packet(bytes)
        trans_id(int): transaction ID
    
    """
    trans_id = random.getrandbits(32)
    ip_address = 0
    key = random.getrandbits(32)
    num_want = DEFAULT_NUM_WANT
    # Q= 64 bit I = 32 bit, H = 16 bit [64,32,32,20bytes,20bytes,64,64,64,32,32,32,32,16], ingesamt 98byte
    struckt_string = ">QII20s20sQQQIIIIH"
    if num_want == -1:
        struckt_string = ">QII20s20sQQQIIIiH"
    packet = struct.pack(struckt_string,
                          con_id, 
                          ACTION_ANNOUNCE, 
                          trans_id, 
                          info_hash, 
                          peer_id, 
                          downloaded, 
                          left, 
                          uploaded, 
                          EVENT_STARTED, 
                          ip_address, 
                          key, 
                          num_want, 
                          DEFAULT_PORT) 

    return packet, trans_id

def generate_peer_id():
    """
    Generates a peer id. https://wiki.theory.org/BitTorrentSpecification#peer_id
    Returns:
        id(bytes)
    """
    start = "-PC0001-"
    length = 12
    random_string = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
    id = start + random_string
    id = id.encode()
    return id



def parse_announce_response(response, expected_trans_id):
    """
    Parses the response of an announce request.
    Parameter:
        response(byte)
        expected_trans_id(int): used for assertion
    Returns: 
        dictionary:
            interval,
            leechers,
            seeders,
            peers
    """

    header = struct.unpack(">IIIII", response[:ANNOUNCE_RESPONSE_HEADER_SIZE])
    action = header[0]
    transaction_id = header[1]
    interval = header[2]
    leechers = header[3]
    seeders = header[4]

    assert transaction_id == expected_trans_id, f"Assert failed! trans_id = {transaction_id}, expected = {expected_trans_id}"

    num_peers = (len(response) - ANNOUNCE_RESPONSE_HEADER_SIZE) // PEER_SIZE # 6 Byte per peer
    peers = []
    for i in range(num_peers):
        start = ANNOUNCE_RESPONSE_HEADER_SIZE + i*PEER_SIZE
        end = start+PEER_SIZE

        peer_data = response[start:end]
        ip_bytes, port = struct.unpack(">4sH", peer_data)

        ip = socket.inet_ntoa(ip_bytes)
        peers.append((ip, port))


    return {
        'interval': interval,
        'leechers': leechers,
        'seeder': seeders,
        'peers': peers
    }

def main():
    "Teste UDP Tracker"
    torrent = torrent_file.parse_torrent_file("linuxmint-22.2-cinnamon-64bit.iso.torrent")
    tracker, port = torrent_file.get_tracker_and_port(torrent)
    packet, expected_transaction_id = build_connect_request()
    response, addr = send_request(tracker, port, packet)
    _, _, con_id = parse_connect_response(response, expected_transaction_id)

    peer_id = generate_peer_id()
    info_hash = torrent_file.calculate_info_hash(torrent['info'])
    downloaded = 0
    size = torrent_file.get_total_size(torrent)
    uploaded = 0

    packet, trans_id = build_announce_request(con_id, info_hash, peer_id, downloaded, size, uploaded)
    response, addr = send_request(tracker, port, packet)
    result = parse_announce_response(response, trans_id)
    print(f"Interval: {result['interval']} seconds")
    print(f"Seeders: {result['seeder']}")
    print(f"Leechers: {result['leechers']}")
    print(f"\nPeers ({len(result['peers'])}):")
    for i, (ip, port) in enumerate(result['peers'][:10], 1):
        print(f"  {i}. {ip}:{port}")

if __name__ == "__main__":
    main()