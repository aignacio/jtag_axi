#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : jtag_base.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
# Date              : 20.09.2024
# Last Modified Date: 20.09.2024
from enum import Enum


_AXI_ADDR_WIDTH = 32
_AXI_DATA_WIDTH = 32


class AccessMode(Enum):
    RW = 1
    RO = 2
    WO = 3


class InstJTAG(Enum):
    # Each entry: (binary_encoding, mask, policy, register_length)
    EXTEST = ("0b0000", 1, AccessMode.RO, 0x1)
    SAMPLE_PRELOAD = ("0b1010", 1, AccessMode.RO, 0xF)
    IC_RESET = ("0b1100", 4, AccessMode.RW, 0xF)
    IDCODE = ("0b1110", 32, AccessMode.RO, 0xFFFF_FFFF)
    BYPASS = ("0b1111", 1, AccessMode.RO, 0x1)
    ADDR_AXI_REG = ("0b0001", 32, AccessMode.RW, 0xFFFF_FFFF)
    DATA_W_AXI_REG = ("0b0010", 32, AccessMode.RW, 0xFFFF_FFFF)
    CTRL_AXI_REG = ("0b0100", 8, AccessMode.RW, 0xC7)
    STATUS_AXI_REG = ("0b0101", 35, AccessMode.RO, 0xFFFF_FFFF)
    WSTRB_AXI_REG = ("0b0011", 4, AccessMode.RW, 0xF)


# JTAG TAP Controller States
class JTAGState(Enum):
    TEST_LOGIC_RESET = 0
    RUN_TEST_IDLE = 1
    SELECT_DR_SCAN = 2
    CAPTURE_DR = 3
    SHIFT_DR = 4
    EXIT1_DR = 5
    PAUSE_DR = 6
    EXIT2_DR = 7
    UPDATE_DR = 8
    SELECT_IR_SCAN = 9
    CAPTURE_IR = 10
    SHIFT_IR = 11
    EXIT1_IR = 12
    PAUSE_IR = 13
    EXIT2_IR = 14
    UPDATE_IR = 15


class AXISize(Enum):
    AXI_BYTE = 0
    AXI_HALF_WORD = 1
    AXI_WORD = 2
    AXI_DWORD = 3
    AXI_BYTES_16 = 4
    AXI_BYTES_32 = 5
    AXI_BYTES_64 = 6
    AXI_BYTES_128 = 7


class TxnType(Enum):
    AXI_READ = 0
    AXI_WRITE = 1


class JDRCtrlAXI:
    def __init__(
        self,
        start=0,
        txn_type=TxnType.AXI_READ,
        fifo_ocup=0,
        size_axi=AXISize.AXI_BYTE,
    ):
        self.start = start & 0x1  # 1 bit
        self.txn_type = txn_type  # 1 bit
        self.fifo_ocup = fifo_ocup & 0x7  # 3 bits
        self.size_axi = size_axi  # 3 bits

    def get_jdr(self):
        """
        Packs the fields into an 8-bit register and returns the formatted value.
        | START [7] | TXN TYPE [6] | fifo_ocup [5:3] | SIZE_AXI [2:0] |
        """
        jdr = (
            (self.start << 7)
            | (self.txn_type.value << 6)
            | (self.fifo_ocup << 3)
            | (self.size_axi.value)
        )
        return jdr

    @classmethod
    def from_jdr(cls, jdr_value):
        """
        Takes an 8-bit value and decodes it into the class attributes.
        """
        start = (jdr_value >> 7) & 0x1
        txn_type = TxnType((jdr_value >> 6) & 0x1)
        fifo_ocup = (jdr_value >> 3) & 0x7
        size_axi = AXISize(jdr_value & 0x7)
        return cls(
            start=start, txn_type=txn_type, fifo_ocup=fifo_ocup, size_axi=size_axi
        )

    def __str__(self):
        return (
            f"START: {self.start}, TXN_TYPE: {self.txn_type.name}, "
            f"fifo_ocup: {self.fifo_ocup}, SIZE_AXI: {self.size_axi.name}"
        )


class JTAGToAXIStatus(Enum):
    JTAG_IDLE = 0
    JTAG_RUNNING = 1
    JTAG_TIMEOUT = 2
    JTAG_AXI_OKAY = 3
    JTAG_AXI_EXOKAY = 4
    JTAG_AXI_SLVERR = 5
    JTAG_AXI_DECERR = 6


def bits_to_ff_hex(num_bits):
    # Calculate the number of bytes needed (each byte is 8 bits)
    num_bytes = (num_bits + 7) // 8  # Add 7 to round up to the nearest byte

    # Create the integer value where all bits are set to 1 for the given number of bytes
    ff_value = (1 << (num_bytes * 8)) - 1

    return ff_value


class JDRStatusAXI:
    def __init__(
        self,
        data_rd=0,
        status=0,
    ):
        self.data_rd = data_rd & bits_to_ff_hex(_AXI_DATA_WIDTH)
        self.status = JTAGToAXIStatus(status & 0x7)  # 3 bit

    def get_jdr(self):
        """
        Packs the fields into an 35-bit register and returns the formatted value.
        | DATA_RD [(_AXI_ADDR_WIDTH+33-1):3] | STATUS [2:0] |
        """
        jdr = (self.data_rd << 3) | (self.status.value << 0)
        return jdr

    @classmethod
    def from_jdr(cls, jdr_value):
        """
        Takes an 35-bit value and decodes it into the class attributes.
        """
        data_rd_new = (jdr_value >> 3) & bits_to_ff_hex(_AXI_DATA_WIDTH)
        status_new = jdr_value & 0x7
        return cls(data_rd=data_rd_new, status=status_new)

    def __str__(self):
        return f"DATA RD: {hex(self.data_rd)}, STATUS: {self.status}"

    def __eq__(self, other):
        if isinstance(other, JDRStatusAXI):
            return self.data_rd == other.data_rd and self.status == other.status
        return False
