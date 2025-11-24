import string
import secrets
from torrent_file import parse_torrent_file, calculate_info_hash, show_torrent_info
from urllib import parse
import requests
from bencode import decode_dict
def generate_peer_id():
    start = "-PC0001-"
    length = 12
    random_string = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
    id = start + random_string
    id = id.encode()
    return id

def build_tracker_url(tracker_url, info_hash, peer_id, port, uploaded, downloaded, left):
    peer_id = parse.quote_from_bytes(peer_id)
    return f"{tracker_url}?info_hash={info_hash}&peer_id={peer_id}&port={port}&uploaded={uploaded}&downloaded={downloaded}&left={left}&compact=1"

def contact_tracker(tracker_url, info_hash, peer_id, port, uploaded, downloaded, left):
    url = build_tracker_url(tracker_url, info_hash, peer_id, port, uploaded, downloaded, left)
    headers = {
        'User-Agent': 'Python-BitTorrent-Client/1.0'
    }
    req = requests.get(url, headers=headers, timeout=10)
    
    if req.status_code != 200:
        raise Exception(f"Tracker error: {req.status_code}")
    
    return req.content  

def find_working_tracker(torrent):
    info_hash = calculate_info_hash(torrent)
    peer_id = generate_peer_id()
    port = 6881
    uploaded = 0
    downloaded = 0
    
    if 'length' in torrent['info']:
        left = torrent['info']['length']
    elif 'files' in torrent['info']:
        left = sum(f['length'] for f in torrent['info']['files'])
    
    # Sammle alle Tracker-URLs
    trackers = []
    
    if 'announce-list' in torrent:

        for tier in torrent['announce-list']:
            for url in tier:
                trackers.append(url)
    elif 'announce' in torrent:

        trackers.append(torrent['announce'])
    else:
        raise Exception("No trackers found in torrent!")
    

    for url in trackers:
        if url.startswith('udp://'):
            continue
        print(f"Trying: {url}")
        try:
            res = contact_tracker(url, info_hash, peer_id, port, uploaded, downloaded, left)
            tracker_data = parse_response(res)
            print(f"Working url {url}")
            return (url, tracker_data)
        except Exception as e:
            print(f" Failed: {e}")
    
    raise Exception("No working tracker found!")


def parse_response(response):
    tracker_data, _ = decode_dict(response.decode('latin-1'), 0)
    if 'failure reason' in tracker_data:
        raise Exception(f"Tracker says: {tracker_data['failure reason']}")
    else:
        print(f"Success! Got peers!")
        return tracker_data


torrent = parse_torrent_file("fun/torrent/debian-13.1.0-amd64-netinst.iso.torrent")

print("All keys in torrent:")
print(torrent.keys())

print("\nAll keys in info:")
print(torrent['info'].keys())

print("\nFull torrent (first level):")
for key in torrent.keys():
    if key == 'info':
        print(f"  {key}: <dict with {len(torrent[key])} keys>")
    else:
        value = torrent[key]
        if isinstance(value, bytes) and len(value) > 50:
            print(f"  {key}: <bytes, {len(value)} bytes>")
        else:
            print(f"  {key}: {value}")
find_working_tracker(torrent)



