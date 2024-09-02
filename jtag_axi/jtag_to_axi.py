#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : jtag_to_axi.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
# Date              : 29.08.2024
# Last Modified Date: 02.09.2024
from pyftdi.ftdi import Ftdi
from pyftdi.jtag import JtagEngine, JtagTool
from os import environ
from pyftdi.bits import BitSequence
import time
# pylint: disable=missing-docstring


# Should match the tested device
JTAG_INSTR = {'SAMPLE': BitSequence('0001', msb=True, length=4),
              'PRELOAD': BitSequence('0001', msb=True, length=4),
              'IDCODE': BitSequence('0100', msb=True, length=4),
              'BYPASS': BitSequence('1111', msb=True, length=4),
              'ADDR_AXI_REGISTER': BitSequence('0001', msb=True, length=4),
              'DATA_AXI_REGISTER': BitSequence('0010', msb=True, length=4),
              'MGMT_AXI_REGISTER': BitSequence('0011', msb=True, length=4)}
# Replace this URL with the one that matches your FT2232 device
FTDI_DEVICE_URL = 'ftdi://ftdi:2232/1'

Ftdi.show_devices()
# Initialize FTDI connection
ftdi = Ftdi()
ftdi.open_from_url(FTDI_DEVICE_URL)

url = environ.get('FTDI_DEVICE', FTDI_DEVICE_URL)
jtag = JtagEngine(trst=False, frequency=1E6)
jtag.configure(url)
jtag.reset()

"""Read the IDCODE right after a JTAG reset"""
jtag.reset()
idcode = jtag.read_dr(32)
print(f'IDCODE (reset): 0x{int(idcode):x}')

"""Test the BYPASS instruction using shift_and_update_register"""
instruction = JTAG_INSTR['BYPASS']
jtag.change_state('shift_ir')
retval = jtag.shift_and_update_register(instruction)
print(f'retval: 0x{int(retval):x}')
jtag.go_idle()
jtag.change_state('shift_dr')
in_ = BitSequence('011011110000'*2, length=24)
out = jtag.shift_and_update_register(in_)
print(f'BYPASS sent:\n{in_}\n{out} '
      f' (should be left shifted by one)')


instruction = JTAG_INSTR['ADDR_AXI_REGISTER']
jtag.change_state('shift_ir')
# jtag.write_ir(instruction)
ret = jtag.shift_and_update_register(instruction)
print(ret)
addr_on = BitSequence('10000000000000000000000000000001', msb=True, length=32)
addr_off = BitSequence('00000000000000000000000000000000', msb=True, length=32)

for i in range(100000):
    print(f"Sending JTAG command no {i}")
    if (i%2) == 0:
        jtag.change_state('shift_dr')
        ret = jtag.shift_and_update_register(addr_on)
    else:
        jtag.change_state('shift_dr')
        ret = jtag.shift_and_update_register(addr_off)
    time.sleep(0.025)

jtag.close()
ftdi.close()
