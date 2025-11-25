from client import *

torrent_file = "linuxmint-22.2-cinnamon-64bit.iso.torrent"
torrent, info_hash = load_torrent(torrent_file)
peers, peer_id = get_peers_from_tracker(torrent, info_hash)
sock = connect_to_peer(peers, info_hash, peer_id)
piece = download_file(sock, torrent, "out.iso")