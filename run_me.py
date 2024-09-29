#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : run_me.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
# Date              : 29.09.2024
# Last Modified Date: 29.09.2024
from jtag_axi import JtagToAXIFTDI
import time
import random

RAM_SIZE = 400 #32*1024 # memory size in bytes
MEM_START_0 = 0x00
MEM_START_1 = 0x10000000
WORD_SIZE = 4

def rnd_val(bit: int = 0, zero: bool = True):
        if zero is True:
            return random.randint(0, (2**bit) - 1)
        else:
            return random.randint(1, (2**bit) - 1)

def initialize_memory(ram_size):
    num_words = ram_size // WORD_SIZE
    memory = [0] * num_words  # Initialize memory with zeroed values
    return memory

def write_to_memory(memory, jtag, offset):
    for i in range(len(memory)):
        random_value = rnd_val(32)
        jtag.write_axi(offset+(i*4), random_value)
        memory[i] = random_value   # Store the value locally for comparison
        # print(f"Writing address {hex(i*4)}, with data {hex(random_value)}")

def read_from_memory(memory, jtag, offset):
    for i in range(len(memory)):
        expected_value = memory[i]
        actual_value = jtag.read_axi(offset+(i*4)).data_rd
        # print(f"Reading address {hex(i*4)}, got data {hex(actual_value)}")
        if expected_value != actual_value:
            print(f"Mismatch at word {i}: expected {hex(expected_value)}, "
                  f"got {hex(actual_value)}")
            return False
    return True

def main():
    jtag = JtagToAXIFTDI(
            device='ftdi://ftdi:2232:3:4/1',
            debug=False,
            freq=10e6
    )
    jtag.read_jdrs()

    print("--------------------------------------")
    print("[Write AXI RAM test] Testing u_imem_1")
    memory = initialize_memory(RAM_SIZE)
    write_to_memory(memory, jtag, MEM_START_0)
    if read_from_memory(memory, jtag, MEM_START_0):
        print("===> Memory check passed! <===")
    else:
        print("Memory check failed!")

    print("--------------------------------------")
    print("[Write AXI RAM test] Testing u_imem_2")
    memory = initialize_memory(RAM_SIZE)
    write_to_memory(memory, jtag, MEM_START_1)
    if read_from_memory(memory, jtag, MEM_START_1):
        print("===> Memory check passed! <===")
    else:
        print("Memory check failed!")


if __name__ == "__main__":
    main()
