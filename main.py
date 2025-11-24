from client import *

torrent, info_hash = load_torrent("linuxmint-22.2-cinnamon-64bit.iso.torrent")
peers, peer_id = get_peers_from_tracker(torrent, info_hash)
sock = connect_to_peer(peers, info_hash, peer_id)
piece = download_piece(sock, 0)
print(f"piece{piece}")