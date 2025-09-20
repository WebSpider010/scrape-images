import httpx
import asyncio
import aiofiles
import json
from jsonpath_ng import parse
from typing import Union
from RotateUserAgent import RotateUserAgent
import ssl, os
try:
    IMAGE_SCRAPER = os.environ["IMAGE_SCRAPER"]
except KeyError:
    IMAGE_SCRAPER = "Token!"
RotateUserAgent.load_user_agents() # Load the user-agents for use

# Information to create a connection with IP address rather than URL
CONNECTION = {
        'ip_address': "151.101.1.181",
        'domain': "unsplash.com",
        'path': "napi/search/photos?page={}&per_page=20&query={}",
        'certif': "unsplash.crt",
    }

HEADERS = {
    "Host": CONNECTION['domain'],
    "User-Agent": RotateUserAgent.get_random(),
    }

def ssl_verification(ip_address: str, port: int, domain: str, certif: str):
    import socket
    try:
        context = ssl.create_default_context(cafile=certif)
    except httpx.ConnectError:
        return False
    context.check_hostname = False
    conn = context.wrap_socket(socket.create_connection((ip_address, port)),server_hostname=domain)
    certif = conn.getpeercert()
    conn.close()

    # Extract the Common Name (CN)
    subject = dict(x[0] for x in certif['subject'])
    common_name = subject.get('commonName')

    # Extract Subject Alternative Names (SANs)
    san = []
    if 'subjectAltName' in certif:
        san = [x[1] for x in certif['subjectAltName'] if x[0] == 'DNS']
    if domain == common_name or domain in san:
        return True
    return False

async def make_request(keyword: str, client: httpx.AsyncClient, page: int =  1) -> dict:
    from urllib.parse import quote
    try:
        path = CONNECTION['path'].format(page, quote(keyword))
        response = await client.get(f"https://{CONNECTION['ip_address']}/{path}", headers=HEADERS, follow_redirects=True)
        if response.status_code != 200:
            print(f"[!] Request fail with STATUS-CODE<{response.status_code}>")
            return
        print(f"[+] Request Made with STATUS-CODE<{response.status_code}>")
        return response.json()
    except httpx.RequestError as e:
        print(f"[!] Request fail with EXCEPTION: {e}")

async def download_image(url: str, client: httpx.AsyncClient, path: str) -> Union[int, None]:
    try:
        async with client.stream("GET", url, timeout=10, follow_redirects=True, headers=HEADERS) as response:
            print(f"[*] Request made to: {url}")
            if response.status_code == 200:
                total_bytes = int(response.headers.get("Content-Length", None))
                total_chunks = 0
                async with aiofiles.open(path, "ab") as image:
                    async for chunck in response.aiter_bytes():
                        if chunck:
                            await image.write(chunck)
                            total_chunks += 1
                        else:
                            print(f"Chunck-{total_chunks} not downloaded")
                print(f"Successfully downloaded image to {path}")
                return total_bytes or total_chunks
            else:
                print(f"Request fail with status code <{response.status_code}>")
    except httpx.RequestError as e:
        print(f"[!] Downloading Fail with exception: {e}")

def generate_keywords():
    keywords = ['conference attendees', 'children face', 'sportsman face', 'man in suit', 'public speaker', 'Asian businessman']
    for keyword in keywords:
        yield keyword

def accept_image(text: str) -> bool:
    face_keywords = [
    # Facial Features
    "face", "eyes", "nose", "mouth", "lips", "cheeks", "chin", "jaw", "forehead", 
    "eyebrows", "eyelashes", "ears", "cheekbones", "dimples", "freckles", 
    "wrinkles", "crow's feet", "smile lines",

    # Eye-Related
    "pupils", "iris", "eyelids", "eye color", "blue eyes", "brown eyes", 
    "green eyes", "hazel eyes", "almond eyes", "round eyes", "deep-set eyes",

    # Nose-Related
    "nostril", "bridge", "aquiline nose", "button nose", "roman nose",

    # Mouth/Lips-Related
    "teeth", "smile", "frown", "pout", "full lips", "thin lips", "cupid's bow",

    # Hair/Facial Hair (often associated with face)
    "hair", "bangs", "sideburns", "beard", "mustache", "stubble", "goatee",

    # Skin and Complexion
    "skin", "complexion", "fair skin", "dark skin", "olive skin", "tanned skin", 
    "blemish", "scar", "mole", "rosy cheeks", "pale skin", "smooth skin",

    # Expressions and Emotions
    "smile", "grimace", "scowl", "smirk", "laugh lines", "expression", 
    "frowning", "grinning", "pouting", "squinting", "winking",

    # Shape and Structure
    "oval face", "round face", "square face", "heart-shaped face", 
    "angular face", "symmetrical face",

    # Other Descriptors
    "portrait", "profile", "visage", "countenance", "gaze", "look", 
    "facial expression", "headshot"
]
    for keyword in face_keywords:
        if keyword in text.lower():
            return True
    return False

def setup_directories():
    if not os.path.exists('images'):
        os.mkdir('images') 
    if not os.path.exists('maps'):
        os.mkdir('maps')
    # for keyword in generate_keywords():
    #     directory = f"images/{keyword.replace(" ", '_')}"
    #     if not os.path.exists(directory):
    #         os.mkdir(directory)

async def extract_data(data: dict):
    pattern = parse("$.results[*]")
    result = []
    #image_links = []
    for item in pattern.find(data):
        item = item.value
        if not item['premium']:
            result.append(
                {
                    'id': item['id'],
                    'url': item['urls']['small'],
                    'headline': item['slug'].replace('-', " "),
                    'height': item['height'],
                    'width': item['width'],
                    'created_at': item['created_at'],
                    'updated_at': item['updated_at'],
                    'description': item['description'] or item['alt_description'],
                    'color': item['color'],
                }
            )
        else:
            print(f"[*] Image <{item['id']}> IN PREMIUM")
    return result
async def main():
    certif = 'unsplash.crt'
    number_of_images = 0
    # Setup directories
    setup_directories()
    if ssl_verification(CONNECTION['ip_address'], 443, CONNECTION['domain'], certif):
        async with httpx.AsyncClient(verify=False) as client:
                for keyword in generate_keywords():
                    images_map = []
                    try:
                        for page in range(1, 21):
                            data = await make_request(keyword, client, page)
                            result = await extract_data(data)
                            number_of_images += len(result)
                            print(f"[*] Number of Images for {keyword}:", len(result))
                            for image in result:
                                path = f"images/{image['id']}.jpg"
                                size = await download_image(f"https://{CONNECTION['ip_address']}/{image['url'].replace('https://unsplash.com/', '')}", client, path)
                                image['path'] = path
                                image['size'] = size
                                image['fom-page'] = page
                                images_map.append(image)
                    except Exception as e:
                        print("Exception: ", e)
                    finally:
                        # Create the plan of images getted
                        async with aiofiles.open(f"maps/map-{keyword}.json", "w", encoding='utf-8') as file:
                            content = json.dumps(images_map, indent=4)
                            await file.write(content)
        print(f"Number of images Downloaded <{number_of_images}>")
    else:
        print("[!] SSL CONNECTION FAIL")
        return

if __name__ == "__main__":
    asyncio.run(main())
