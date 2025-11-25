import torrent_file
import udp_tracker
import peer_protocol

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

def download_piece(sock, piece_index, torrent):

    peer_protocol.send_interested(sock)
    print("Sent: interested")
    
    message_id, payload = peer_protocol.receive_message(sock)
    print(f"1. Received: message_id={message_id}")

    piece_data = b''
    piece_length = peer_protocol.get_piece_length(torrent, piece_index)
    num_blocks = (piece_length + 16383) // 16384 

    for block_num in range(num_blocks):
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

    print(f"\nPiece Data Length: {len(piece_data)} bytes")
    print(f"Expected: {torrent['info']['piece length']} bytes")
    pieces_hashes = torrent['info']['pieces']
    expected_hash = pieces_hashes[piece_index*20: piece_index*20+20]
    if isinstance(expected_hash, str):
        expected_hash = expected_hash.encode('latin-1')
    if peer_protocol.validate_piece(piece_data, expected_hash):
        print("Piece ok!")
        return piece_data
    else:
        raise Exception("Fehler: Hash of piece does not match the expected hash.")
        
def download_file(sock, torrent, output_filename):
    """
    Downloaded alle Pieces und schreibt sie in eine Datei
    
    Parameters:
        sock: Socket-Verbindung zum Peer
        torrent: Parsed torrent dict
        output_filename: Wo die Datei gespeichert wird
    """
    num_pieces = len(torrent['info']['pieces']) // 20

    for piece in range(num_pieces):
        piece_length = peer_protocol.get_piece_length(torrent, piece)
        piece_data = download_piece(sock, piece, torrent)
        with open(output_filename, "wb") as f:
            f.seek(piece * piece_length)
            f.write(piece_data)
        print(f"Downloaded piece {piece}/{num_pieces}")