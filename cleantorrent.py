#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import random
import string
from os import path


class BTFailure(Exception):
    pass


def random_string():
    r = ''.join(
        random.choice(
            string.ascii_uppercase +
            string.digits) for x in range(6))
    return r


def trash_useless(data):  # dump useless info
    keys = [
        'publisher-url',
        'publisher',
        'publisher-url.utf-8',
        'publisher.utf-8',
        'name.utf-8', ]
    for k in keys:
        if k in data['info']:
            data['info'].pop(k)
    if 'comment' in data:
        data.pop('comment')
    return data


# differents see
# https://wiki.theory.org/BitTorrentSpecification#Info_Dictionary


def single_file(info):
    dot_index = info['name'].rfind(".")  # find the last . in the file
    if dot_index != -1:
        # random file name
        info['name'] = random_string() + info['name'][dot_index:]
    return info


def multi_file(info):
    info['name'] = random_string()
    for i in info['files']:
        if 'path' in i:
            i['path'] = short_and_random(i)
        if 'path.utf-8' in i:
            i.pop('path.utf-8')
    return info


def short_and_random(item):
    # the file is the last one of a path list
    dot_index = item['path'][-1].rfind(".")
    if dot_index != -1:
        # no more folder just file
        return [random_string() + item['path'][-1][dot_index:]]


def clean_torrent(filepath):
    try:
        torrent = open(filepath, "rb")
    except IOError:
        print("error, can not open torrent file.")
    else:
        try:
            decoded_data = bdecode(torrent.read())
            old_info = decoded_data['info']
        except BTFailure:
            print("error, not a valid torrent.")
        else:
            if 'files' in old_info:
                decoded_data['info'] = multi_file(old_info)
            else:
                decoded_data['info'] = single_file(old_info)
            split_path = path.split(path.abspath(filepath))
            new_torrent = open(path.join(split_path[0], 'new_' + split_path[1]), "wb")
            new_torrent.write(bencode(trash_useless(decoded_data)))
            new_torrent.close()
            torrent.close()


def decode_int(x, f):
    f += 1
    newf = x.index('e', f)
    n = int(x[f:newf])
    if x[f] == '-':
        if x[f + 1] == '0':
            raise ValueError
    elif x[f] == '0' and newf != f + 1:
        raise ValueError
    return (n, newf + 1)


def decode_string(x, f):
    colon = x.index(':', f)
    n = int(x[f:colon])
    if x[f] == '0' and colon != f + 1:
        raise ValueError
    colon += 1
    return (x[colon:colon + n], colon + n)


def decode_list(x, f):
    r, f = [], f + 1
    while x[f] != 'e':
        v, f = decode_func[x[f]](x, f)
        r.append(v)
    return (r, f + 1)


def decode_dict(x, f):
    r, f = {}, f + 1
    while x[f] != 'e':
        k, f = decode_string(x, f)
        r[k], f = decode_func[x[f]](x, f)
    return (r, f + 1)


decode_func = {}
decode_func['l'] = decode_list
decode_func['d'] = decode_dict
decode_func['i'] = decode_int
decode_func['0'] = decode_string
decode_func['1'] = decode_string
decode_func['2'] = decode_string
decode_func['3'] = decode_string
decode_func['4'] = decode_string
decode_func['5'] = decode_string
decode_func['6'] = decode_string
decode_func['7'] = decode_string
decode_func['8'] = decode_string
decode_func['9'] = decode_string


def bdecode(x):
    try:
        r, l = decode_func[x[0]](x, 0)
    except (IndexError, KeyError, ValueError):
        raise BTFailure("not a valid bencoded string")
    if l != len(x):
        raise BTFailure("invalid bencoded value (data after valid prefix)")
    return r


from types import StringType, IntType, LongType, DictType, ListType, TupleType


class Bencached(object):
    __slots__ = ['bencoded']

    def __init__(self, s):
        self.bencoded = s


def encode_bencached(x, r):
    r.append(x.bencoded)


def encode_int(x, r):
    r.extend(('i', str(x), 'e'))


def encode_bool(x, r):
    if x:
        encode_int(1, r)
    else:
        encode_int(0, r)


def encode_string(x, r):
    r.extend((str(len(x)), ':', x))


def encode_list(x, r):
    r.append('l')
    for i in x:
        encode_func[type(i)](i, r)
    r.append('e')


def encode_dict(x, r):
    r.append('d')
    ilist = x.items()
    ilist.sort()
    for k, v in ilist:
        r.extend((str(len(k)), ':', k))
        encode_func[type(v)](v, r)
    r.append('e')


encode_func = {}
encode_func[Bencached] = encode_bencached
encode_func[IntType] = encode_int
encode_func[LongType] = encode_int
encode_func[StringType] = encode_string
encode_func[ListType] = encode_list
encode_func[TupleType] = encode_list
encode_func[DictType] = encode_dict

try:
    from types import BooleanType

    encode_func[BooleanType] = encode_bool
except ImportError:
    pass


def bencode(x):
    r = []
    encode_func[type(x)](x, r)
    return ''.join(r)


if __name__ == '__main__':
    fileList = os.listdir(os.getcwd())
    for filePath in fileList:
        clean_torrent(filePath)