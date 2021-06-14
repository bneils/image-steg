#!/usr/bin/env python
# Author: Ben Neilsen
# Description: A tool for hiding a file in an image
from PIL import Image
import argparse
import numpy as np

# How encoding works:
#  bitwidth = 2^(exponent)
#  You can choose to leave a footprint that encodes the bitwidth in the first byte, and the NUL-terminated file name in a few other bytes. 
#  This is optional, but if you do this, you must remember to decode it with this program, or another program that does the same thing (unlikely).
#  You must choose a bitwidth (default 1) to encode in. The higher this number, the more noticable the steganography is.

def bititer(nums, count=1):
    if count not in (1, 2, 4, 8):
        raise ValueError('bitwidth may only be power of 2 that is <= 8')
    mask = ~(~0 << count)
    shifts = range(8 - count, -1, -count)
    return np.asarray([n >> shift & mask for n in nums for shift in shifts], dtype=np.uint8)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Hide files in images')
    parser.add_argument('file', type=str, help='the path to the file to be hidden')
    parser.add_argument('image', type=str, help='the path to the image')
    parser.add_argument('bitwidth', type=int, help='the bitwidth to use')
    parser.add_argument('-f', '--footprint', action='store_true', help='records bitwidth and file name')
    parser.add_argument('-o', '--output', type=str, default='out.png', help='file name of result')
    args = parser.parse_args()

    if args.bitwidth not in (1, 2, 4, 8):
        raise argparse.ArgumentError('Invalid bitwidth: %d' % args.bitwidth)

    with open(args.file, 'rb') as f:
        src = f.read()
    src = bytes(len(src)) + bytes(args.file) + src

    image = Image.open(args.image)
    dest = np.array(image)
    dest = dest.reshape(dest.size)
    if len(src) > dest.size * 8 // args.bitwidth:
        raise ValueError("Not enough space")
    
    if args.footprint:
        start = 1
        dest[0] = dest[0] & ~0b11 | (1, 2, 4, 8).index(args.bitwidth)
    else:
        start = 0

    end = len(src) * 8 // args.bitwidth + start

    # Apply mask of bitwidth num 1s to area
    dest[start:end] &= np.uint8(~0 << args.bitwidth)

    # Set bits
    dest[start:end] |= bititer(src, args.bitwidth)

    # Save result
    result = Image.frombytes(image.mode, image.size, dest)
    result.save(args.output)