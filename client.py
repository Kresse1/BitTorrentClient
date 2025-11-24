import torrent_file
import udp_tracker
import peer_protocol
import struct

def load_torrent(file):
    torrent = torrent_file.parse_torrent_file(file)
    info_hash = torrent_file.calculate_info_hash(torrent['info'])
    return torrent, info_hash

def get_peers_from_tracker(torrent, info_hash):
    """Kontaktiert Tracker, gibt Peer-Liste zurück"""    
    tracker, port = torrent_file.get_tracker_and_port(torrent)
    packet, expected_transaction_id = udp_tracker.build_connect_request()
    response, addr = udp_tracker.send_request(tracker, port, packet)
    _, _, con_id = udp_tracker.parse_connect_response(response, expected_transaction_id)
    peer_id = udp_tracker.generate_peer_id()
    
    downloaded = 0
    size = torrent_file.get_total_size(torrent)
    uploaded = 0
    packet, trans_id = udp_tracker.build_announce_request(con_id, info_hash, peer_id, downloaded, size, uploaded)
    response, addr = udp_tracker.send_request(tracker, port, packet)
    result = udp_tracker.parse_announce_response(response, trans_id)
    peers = result['peers']
    print(f"Found {len(peers)} peers")
    return peers, peer_id

def connect_to_peer(peers, info_hash, peer_id):
    """Findet funktionierenden Peer, macht Handshake"""
    sock, peer_info = peer_protocol.find_working_peer(peers, info_hash, peer_id)
    message_id, payload = peer_protocol.receive_message(sock)
    print(f"Received: message_id={message_id}, payload_len={len(payload)}")
    return sock

def download_piece(sock, piece_index):
    peer_protocol.send_interested(sock)
    print("Sent: interested")
    
    message_id, payload = peer_protocol.receive_message(sock)
    print(f"1. Received: message_id={message_id}")

    piece_data = b''

    for block_num in range(32):
        begin = block_num * 16384
        peer_protocol.send_request(sock, piece_index, begin)
        print(f"Send request for piece index {piece_index}")


        for i in range(5):  # Falls ein Choke kommt 
            message_id, payload = peer_protocol.receive_message(sock)
            print(f"{i+2}. Received: message_id={message_id}, payload_len={len(payload)}")
            if message_id == 7:
                piece_index, begin, block_data = peer_protocol.parse_piece(payload)
                piece_data += block_data
                break
    return piece_data
        