import hashlib
from bencode import bencode_encode, decode_dict
from urllib import parse
import secrets
import string

def parse_torrent_file(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data)} bytes")
    print("Starting parse...")
    

    torrent_data, length = decode_dict(data.decode('latin-1'), 0)
    
    print(f"Parsed {length} characters")
    return torrent_data

def show_torrent_info(torrent_data):
    print("=" * 50)
    print("TORRENT INFO")
    print("=" * 50)
    print(f"Tracker: {torrent_data['announce']}")
    
    info = torrent_data['info']
    print(f"\nFile Info:")
    print(f"  Name: {info['name']}")
    print(f"  Piece Length: {info['piece length']} bytes")
    
    # Single-File oder Multi-File?
    if 'length' in info:
        # Single-File
        print(f"  Type: Single File")
        print(f"  Size: {info['length']} bytes ({info['length'] / (1024*1024):.2f} MB)")
    elif 'files' in info:
        # Multi-File
        print(f"  Type: Multi-File")
        print(f"  Number of Files: {len(info['files'])}")
        total_size = sum(f['length'] for f in info['files'])
        print(f"  Total Size: {total_size} bytes ({total_size / (1024*1024):.2f} MB)")
        print(f"\n  Files:")
        for i, file in enumerate(info['files'][:5], 1):  # Zeige ersten 5
            path = '/'.join(file['path'])
            print(f"    {i}. {path} - {file['length']} bytes")
        if len(info['files']) > 5:
            print(f"    ... and {len(info['files']) - 5} more files")
    
    num_pieces = len(info['pieces']) // 20
    print(f"\n  Number of Pieces: {num_pieces}")


def calculate_info_hash(info_dict):
    """
    Berechnet den SHA1-Hash des bencodeten info-Dictionarys
    """
    bencoded_info = bencode_encode(info_dict)
    info_hash = hashlib.sha1(bencoded_info).digest()
    return info_hash

def get_tracker_and_port(torrent_data):
    tracker = torrent_data['announce']
    tracker = tracker[6:]
    tracker, port = tracker.split(":")
    port = port.split("/")
    port = port[0]
    port = int(port)
    return tracker, port

def get_total_size(torrent_data):
    info = torrent_data['info']
    if 'length' in info:
        return info['length']
    elif 'files' in info:
        total_size = sum(f['length'] for f in info['files'])
        return total_size
    

    
#torrent = parse_torrent_file("tears-of-steel.torrent")
#info_hash = calculate_info_hash(torrent['info'])
#show_torrent_info(torrent)
#print(get_tracker_and_port(torrent))
#print(f"Info Hash (hex): {info_hash.hex()}")
#print(f"Info Hash (bytes): {info_hash}")
#print(f"Length: {len(info_hash)} bytes")  # Sollte 20 sein!
