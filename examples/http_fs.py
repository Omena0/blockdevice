import time
from typing import List

import requests

from blockdevice import *

dev = BlockDevice("/mnt/http", name="Http")

def path_to_url(fpath: str) -> str:
    # /mnt/http/https/example.com/path1/path2/?/key=value/key2=value2
    # https://example.com/test?key=value&key2=value2
    fpath = fpath.removesuffix('/@')

    fpath = fpath.strip('/')
    proto, domain, *rest = fpath.split('/')

    # Locate query string (first path segment starting with ?)
    query_idx = next((i for i, part in enumerate(rest) if part.startswith('?')), None)

    if query_idx is None:
        path = rest
        query = ''
    else:
        path = rest[:query_idx]
        query_parts = rest[query_idx:]
        query = '&'.join(query_parts)
        query = '?' + query.lstrip('?&')

    url = f'{proto}://{domain}'
    if path_str := '/'.join(path):
        url += f'/{path_str}'
    return url + query

cache = {}

def cache_add(path: str, content: bytes) -> dict:
    cache[path] = {
        "content": content,
        "size": len(content),
        "time": time.time()
    }
    return cache[path]

def cache_fetch(path: str) -> dict:
    url = path_to_url(path)
    try:
        content = requests.get(url).content
    except Exception as e:
        content = str(e).encode()

    return cache_add(path, content)

def cache_get(path: str) -> dict:
    if path not in cache:
        cache_fetch(path)

    entry = cache[path]

    if time.time() - entry['time'] > 3600:
        print('Refreshing..')
        entry = cache_fetch(path)

    return entry

@dev.read
def read(path: str) -> bytes:
    print(f'Read: {path}')

    if path.endswith('/@'):
        path = path.removesuffix('/@')

    return cache_get(path)['content']

@dev.write
def write(path: str, data: bytes) -> bool:
    path = path_to_url(path)

    req = requests.post(path, data)
    return req.ok

@dev.delete
def delete(path: str) -> bool:
    if path.endswith('/@'):
        path = path.removesuffix('/@')

    url = path_to_url(path)

    try:
        req = requests.delete(url)
        if req.ok and path in cache:
            del cache[path]
        return req.ok
    except Exception:
        return False

@dev.stat
def stat_f(path: str) -> StatResult:
    if not path.endswith('/@'):
        return StatResult(
            mode=FileMode(
                type='dir'
            )
        )

    path = path.removesuffix('/@')
    print(f'Stat: {path}')
    entry = cache_get(path)

    return StatResult(
        mode=FileMode(
            type='file'
        ),
        size=entry['size']
    )

@dev.list
def list(path: str) -> List[str]:
    print(f'List: {path}')
    parent = path.rstrip('/')
    prefix = f'{parent}/' if parent else '/'
    children = set()
    for p in cache:
        if p.startswith(prefix) and p != parent:
            rest = p[len(prefix):]
            if not rest:
                continue
            child = rest.split('/')[0]
            children.add(f'{child}/')

    if not children:
        return ['http/', 'https/'] if path == '/' else []

    return sorted(children)

dev.start(True)
