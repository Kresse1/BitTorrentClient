import struct
import socket
import udp_tracker
import torrent_file

def build_handshake(info_hash, peer_id):
    """    
    Parameters:
        info_hash (bytes): 20-byte SHA1-Hash
        peer_id (bytes): 20-byte Peer-ID
        
    Returns:
        bytes: 68-byte Handshake-Message
    """
    packet = struct.pack('B', 19) + b"BitTorrent protocol" + b'\x00'*8 + info_hash + peer_id
    return packet


def send_handshake(peer_ip, peer_port, info_hash, peer_id, timeout=15.0):
    """
    Verbindet zu einem Peer und tauscht Handshakes aus.
    
    Parameters:
        peer_ip (str): IP-Adresse des Peers
        peer_port (int): Port des Peers
        info_hash (bytes): 20-byte SHA1-Hash
        peer_id (bytes): 20-byte Peer-ID
        timeout (float): Connection timeout
        
    Returns:
        tuple: (socket, peer_handshake: bytes)
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    print("Shake hands with",peer_ip, peer_port)

    sock.connect((peer_ip, peer_port))
    handshake = build_handshake(info_hash, peer_id)
    sock.sendall(handshake)
    peer_handshake = sock.recv(68)

    return (sock, peer_handshake)




def parse_handshake(handshake_data, info_hash_og):
    """
    Parst eine empfangene Handshake-Message.
    
    Parameters:
        handshake_data (bytes): 68-byte Handshake vom Peer
        
    Returns:
        dict: {'protocol': str, 'info_hash': bytes, 'peer_id': bytes}
    """
    assert len(handshake_data) == 68, f'Size of handshake is expected to be 68, but is {len(handshake_data)}'
    
    unpack = struct.unpack(">B19s8s20s20s", handshake_data)
    length = unpack[0]
    protocol = unpack[1]
    reserved = unpack[2]
    info_hash = unpack[3]
    peer_id = unpack[4]

    assert length == 19, f"length is expedted to be 19, but is {length}."
    assert protocol == b"BitTorrent protocol", f"s is expected to be b\"BitTorrent protocol\", but is {protocol}."
    assert info_hash == info_hash_og, "Info hashes are not equal"

    dic = {'protocol': protocol, 'info_hash': info_hash, 'peer_id': peer_id}
    
    return dic

def find_working_peer(peers, info_hash, peer_id):
    "Probiert peers bis einer antwortet."

    for peer_ip, peer_port in peers:
        print(f"Try {peer_ip}: {peer_port}...")

        try:
            sock, peer_handshake = send_handshake(peer_ip, peer_port, info_hash, peer_id)
            #Parse
            peer_info = parse_handshake(peer_handshake, info_hash)
            print(f"Erfolgreicher Handshake mit {peer_ip}:{peer_port}")
            print(f"Peer ID: {peer_info['peer_id']}")

            return sock, peer_info
        except Exception as e:
            print(f"Fehler: {e}")
            continue


def recv_exact(sock, n):
    """Empfängt exakt n bytes (robuster als sock.recv)"""
    data = b''
    while len(data) < n:
        chunk = sock.recv(n-len(data))
        if not chunk:
            raise Exception("Connection closed")
        data += chunk
    return data

def recieve_message(sock):
    """
    Empfängt eine BitTorrent-Message vom Peer.
    
    Parameters:
        sock: TCP-Socket-Verbindung
        
    Returns:
        tuple: (message_id: int, payload: bytes)
    """

    # Format: Bytes 0-3, Länge message, Byte 4 message_id (Typ), Bytes 5+ payload
    length_bytes = recv_exact(sock, 4)
    length = struct.unpack('>I', length_bytes)
    length = length[0]
    unpack = recv_exact(sock, length)

    message_id = unpack[0]
    payload = unpack[1:]

    return  message_id, payload



def main():
    torrent = torrent_file.parse_torrent_file("linuxmint-22.2-cinnamon-64bit.iso.torrent")
    tracker, port = torrent_file.get_tracker_and_port(torrent)
    packet, expected_transaction_id = udp_tracker.build_connect_request()
    response, addr = udp_tracker.send_request(tracker, port, packet)
    _, _, con_id = udp_tracker.parse_connect_response(response, expected_transaction_id)

    peer_id = udp_tracker.generate_peer_id()
    info_hash = torrent_file.calculate_info_hash(torrent['info'])
    downloaded = 0
    size = torrent_file.get_total_size(torrent)
    uploaded = 0
    packet, trans_id = udp_tracker.build_announce_request(con_id, info_hash, peer_id, downloaded, size, uploaded)
    response, addr = udp_tracker.send_request(tracker, port, packet)
    result = udp_tracker.parse_announce_response(response, trans_id)

    peers = result['peers']
    print(f"Found {len(peers)} peers")

    sock, peer_info = find_working_peer(peers, info_hash, peer_id)
    print(recieve_message(sock))


        

if __name__ == "__main__":
    main()