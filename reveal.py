#!/usr/bin/env python3
# Author: Ben Neilsen
# Description: A tool for revealing a file from an image
from PIL import Image
import argparse

# Decoding works like:
#  If the program decodes with a flag `footprinted', then it reads the first byte as if it were a footprint left by the encoder to get the bitwidth exponent.
#  bitwidth = 2^(exponent)
#  Additionally, the program assumes that the bitwidth is followed by a file name.
# 
#  For compatibility, you can decode the file normally, but this will have weird results if:
#    The file has a footprint from this program
#    The file has a different bitwidth