import argparse
import datetime
import os
import time
from io import BytesIO

import requests

_units = dict(d=60*60*24, h=60*60, m=60, s=1)
def makedelta(deltavalue):
    seconds = 0
    defaultunit = unit = _units['m']  # default to minutes
    value = ''
    for ch in list(str(deltavalue).strip()):
        if ch.isdigit():
            value += ch
            continue
        if ch in _units:
            unit = _units[ch]
            if value:
                seconds += unit * int(value)
                value = ''
                unit = defaultunit
            continue
        if ch in ' \t':
            # skip whitespace
            continue
        raise ValueError('Invalid time delta: %s' % deltavalue)
    if value:
        seconds = unit * int(value)
    return datetime.timedelta(seconds=seconds)


parser = argparse.ArgumentParser(description='Downloads the most recent Instagram images. Uses the accesstoken(s) from the specified file.')

parser.add_argument('filename', type=str, help='A whitespace delimited file containing access tokens to download images from.')
parser.add_argument('--imagedir', type=str, default='.', help='Where to put the downloaded images. Defaults to the current directory.')
parser.add_argument('--proxy', '-p', type=str, metavar='URI', help='An URI to the proxy server.')
parser.add_argument('--interval', '-i', type=makedelta, metavar='timedelta', default='1m', help='How often this script will connect and download images. Only useful when in combination with --forever or --repeat > 1')
parser.add_argument('--imagecount', type=int, default=20, choices=range(1, 21), help='The number of images to download from each user.')
group = parser.add_mutually_exclusive_group()
group.add_argument('--repeat', '-r', type=int, default=1, metavar='N', help='This will make the script run N times.')
group.add_argument('--forever', '-f', action='store_true', help='This will make the script run forever.')

args = parser.parse_args()

proxies = {
    'http': '',
    'https': ''
}

if args.proxy != None:
    proxies['http'] = args.proxy
    proxies['https'] = args.proxy

if not os.path.isdir(args.imagedir):
    os.makedirs(args.imagedir)

i = args.repeat

while args.forever or i > 0:
    i = i - 1

    with open(args.filename, 'r') as f:
        accesstokens = f.read().splitlines()
    
    imagecount = args.imagecount
    
    for accesstoken in accesstokens:
        recentMedia = requests.get('https://api.instagram.com/v1/users/self/media/recent/?access_token=' + accesstoken, proxies=proxies)
        recentMedia.raise_for_status()

        images = [(os.path.join(args.imagedir, item['id'] + '.jpg'), item['images']['standard_resolution']['url']) for item in recentMedia.json()['data'][0: args.imagecount]]

        for image in images:
            if not os.path.isfile(image[0]):
                imageData = requests.get(image[1], proxies=proxies)
                imageData.raise_for_status()

                with open(image[0], 'wb') as file:
                    file.write(BytesIO(imageData.content).read())

    if args.forever or i > 0:
        time.sleep(args.interval.total_seconds())
