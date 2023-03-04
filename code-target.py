# SPDX-FileCopyrightText: Copyright 2023 Neradoc, https://neradoc.me
# SPDX-License-Identifier: MIT
import board
import time
from i2ctarget import I2CTarget

song_names = [
    "Yellow Submarine",
    "Bohemian Rhapsody",
    "Vivaldi's Four Seasons",
]
current_song = None

"""
Format:
"""
GET_CURRENT_SONG = 0x01 # request current playing song
GET_SONG_NAME    = 0x02 # nn : request name of song nn
DATA_READY       = 0x03 # if the data is ready
GET_SONG_ASYNC   = 0x04 # start a get song async (use data ready and read)

current_sending_data_candidate = None # would be the request to the MP3 player
current_sending_data = b""
out_cursor = 0
sending_data_ready = False
command = None
waiting_command = 0
# simulate retrieving the data taking time
next_ready = 0

index = 0
with I2CTarget(board.SCL, board.SDA, (0x40,)) as device:
    while True:
        if current_sending_data_candidate and time.monotonic() > next_ready:
            time.sleep(0.001)
            current_sending_data = current_sending_data_candidate
            current_sending_data_candidate = None
            sending_data_ready = True
            next_ready = 0

        r = device.request()
        if not r:
            # Maybe do some housekeeping
            continue
        with r:  # Closes the transfer if necessary by sending a NACK or feeding dummy bytes
            if r.address == 0x40:
                if not r.is_read:  # Main write which is Selected read
                    command = r.read(1)[0]
                    print("read", command)
                    if command == GET_SONG_NAME:
                        b = r.read(2)
                        index = int.from_bytes(b, "big")
                        print("index", index)
                        if index < len(song_names):
                            current_sending_data = song_names[index].encode()
                        else:
                            current_sending_data = b""
                        sending_data_ready = True
                        out_cursor = 0
                    if command == GET_SONG_ASYNC:
                        b = r.read(2)
                        index = int.from_bytes(b, "big")
                        print("index", index)
                        if index < len(song_names):
                            current_sending_data_candidate = song_names[index].encode()
                            waiting_command = command
                            sending_data_ready = False
                            next_ready = time.monotonic() + 2
                        else:
                            current_sending_data = b""
                            sending_data_ready = True
                            next_ready = 0
                        out_cursor = 0
                    if command == DATA_READY:
                        pass
                elif r.is_restart:  # Combined transfer: This is the Main read message
                    print("Restart", bytes([regs[index]]))
                    n = r.write(bytes([regs[index]]))
                else:
                    print("Is read", command, index, out_cursor)
                    if command == DATA_READY:
                        is_ready = bytes([int(sending_data_ready)])
                        print(is_ready)
                        r.write(is_ready)
                        command = waiting_command
                    elif command == GET_SONG_NAME or command == GET_SONG_ASYNC:
                        if sending_data_ready:
                            if out_cursor == 0:
                                r.write(bytes([len(current_sending_data)]))
                            if out_cursor < len(current_sending_data) + 1:
                                r.write(current_sending_data[out_cursor-1:out_cursor])
                            elif out_cursor == len(current_sending_data) + 1:
                                print("end string")
                                r.write(b"\x00")
                                sending_data_ready = False
                            else:
                                sending_data_ready = False
                                r.write(b"\xFF")
                        else:
                            r.write(b"\xFF")
                        out_cursor = out_cursor + 1

