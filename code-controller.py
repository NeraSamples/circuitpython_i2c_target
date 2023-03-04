# SPDX-FileCopyrightText: Copyright 2023 Neradoc, https://neradoc.me
# SPDX-License-Identifier: MIT
import board
from adafruit_bus_device.i2c_device import I2CDevice
import binascii
import time

ADDRESS = 0x40

GET_CURRENT_SONG = 0x01 # request current playing song
GET_SONG_NAME    = 0x02 # nn : request name of song nn
DATA_READY       = 0x03 # if the data is ready
GET_SONG_ASYNC   = 0x04 # start a get song async (use data ready and read)

i2c = board.STEMMA_I2C()
device = I2CDevice(i2c, ADDRESS)

with device as bus:
    # request the 2nd song name
    out_buffer = bytearray([GET_SONG_NAME, 0x00])
    in_buffer = bytearray(32)

    print("-"*70)
    print("Write then read")
    print("-"*70)

    # write, then read back
    for i in range(100):
        out_buffer[1] = i
        bus.write_then_readinto(out_buffer, in_buffer)
        if in_buffer[0] == 0:
            break
        length = in_buffer[0]
        try:
            print(bytes(in_buffer)[1:length+2].decode())
        except Exception:
            print("!!", in_buffer)

    print("-"*70)
    print("Write and read separately")
    print("-"*70)

    # write, then read back
    out_buffer[0] = GET_SONG_ASYNC
    for i in range(100):
        print("Song", i + 1)
        out_buffer[1] = i
        bus.write(out_buffer)
        while True:
            time.sleep(0.001)
            bus.write_then_readinto(bytes([DATA_READY]), in_buffer, in_end=1)
            if in_buffer[0] == 1:
                break
        bus.readinto(in_buffer)
        if in_buffer[0] == 0:
            break
        length = in_buffer[0]
        print(bytes(in_buffer)[1:length+2].decode())
        # time.sleep(1)

    print("-"*70)

