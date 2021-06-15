#!/usr/bin/env python
# Author: Ben Neilsen
# Description: A tool for hiding and revealing files inside images

import argparse
import os

import numpy as np
from PIL import Image

def bititer(nums, count=1):
    """Iterate through the bits of a list of 8bit nums, in big-endian order"""
    if count not in (1, 2, 4, 8):
        raise ValueError('bitwidth may only be power of 2 that is <= 8')
    mask = ~(~0 << count)
    shifts = range(8 - count, -1, -count)
    return np.asarray([n >> shift & mask for n in nums for shift in shifts], dtype=np.uint8)


def byteiter(bits, count=1):
    """Combine bits in pairs of `count` and return an array of bytes"""
    if count not in (1, 2, 4, 8):
        raise ValueError('bitwidth may only be power of 2 that is <= 8')
    nums = []
    step = 8 // count
    for i in range(0, len(bits), step):
        nums.append(int(''.join([bin(n)[2:].rjust(count, '0') for n in bits[i:i + step]]), 2))
    return nums

def decode(impath, infer=False, bitwidth=None):
    if not infer and not bitwidth:
        raise ValueError('bitwidth not given and not allowed to make inferences')
    
    image = Image.open(impath)
    data = np.array(image)
    data = data.reshape(data.size)
    if infer:
        # Get bitwidth
        bitwidth = 1 << (data[0] & 0b11)
        start = 1
    else:
        start = 0
    mask = ~(~0 << bitwidth)
    data &= mask
    data = byteiter(data[start:], bitwidth)
    extEndPos = data.index(0)
    ext = ''.join(map(chr,data[:extEndPos]))
    size = data[extEndPos + 1:extEndPos + 1 + 4]
    size = size[0] << 24 | size[1] << 16 | size[2] << 8 | size[3]
    data = bytes(data[extEndPos + 1 + 4:extEndPos + 1 + 4 + size])
    with open('out.' + ext, 'wb') as f:
        f.write(data)

def encode(fp, impath, bitwidth, footprint=False):
    """Encode a file into an image"""
    if bitwidth not in (1, 2, 4, 8):
        raise ValueError('bitwidth not power of 2 at most 8')

    with open(fp, 'rb') as f:
        src = f.read()

    image = Image.open(impath)
    dest = np.array(image)
    dest = dest.reshape(dest.size)
    if len(src) > dest.size * 8 // args.bitwidth:
        raise ValueError('not enough space')
    
    # The footprint should store bitwidth (2 bits at 2 bits/byte), size (32 bits at bitwidth/byte), 
    # file name ((8*chars+1) bits at bitwidth/byte), and content
    # The file name is nul-terminated.
    if footprint:
        start = 1
        ext = bytes(os.path.splitext(fp)[1][1:] + '\0', encoding='utf8')
        src = ext + len(src).to_bytes(4, 'big') + src
        dest[0] = dest[0] & ~0b11 | (1, 2, 4, 8).index(bitwidth)
    else:
        start = 0

    end = len(src) * 8 // bitwidth + start

    # Apply mask of bitwidth num 1s to area
    dest[start:end] &= np.uint8(~0 << bitwidth)

    # Set bits
    dest[start:end] |= bititer(src, bitwidth)
    return Image.frombytes(image.mode, image.size, dest)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    actions = parser.add_subparsers(dest='action', required=True)

    # Parser for encoding
    encode_parser = actions.add_parser('encode')
    encode_parser.add_argument('file', type=str, help='the path to the file to be hidden')
    encode_parser.add_argument('image', type=str, help='the path to the image')
    encode_parser.add_argument('bitwidth', type=int, choices=[1, 2, 4, 8], help='the bitwidth to use')
    encode_parser.add_argument('-f', '--footprint', action='store_true', help='records bitwidth and file name')
    encode_parser.add_argument('-o', '--output', type=str, default='out.png', help='file name of result')

    # Parser for decoding
    decode_parser = actions.add_parser('decode')
    decode_parser.add_argument('image', type=str, help='the path to the image')
    decode_parser.add_argument('-o', '--output', type=str, default='out', help='file name of result')

    action = decode_parser.add_mutually_exclusive_group(required=True)
    action.add_argument('-b', '--bitwidth', type=int, help='the bitwidth to use')
    action.add_argument('-f', '--footprint', action='store_true', help='infer bitwidth, extension, and size')

    args = parser.parse_args()
    
    try:
        if args.action == 'encode':    
            encode(args.file, args.image, args.bitwidth, args.footprint).save(args.output)
        elif args.action == 'decode':
            decode(args.image, args.footprint, args.bitwidth)
    except ValueError as e:
        parser.error(str(e))
