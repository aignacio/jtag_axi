#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : jtag_base.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
# Date              : 20.09.2024
# Last Modified Date: 30.09.2024
from enum import Enum
from abc import abstractmethod

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
    STATUS_AXI_REG = ("0b0101", 36, AccessMode.RO, 0xF_FFFF_FFFF)
    WSTRB_AXI_REG = ("0b0011", 4, AccessMode.RW, 0xF)
    USERCODE = ("0b0111", 32, AccessMode.RO, 0xFFFF_FFFF)


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
    JTAG_TIMEOUT_AR = 2
    JTAG_TIMEOUT_R = 3
    JTAG_TIMEOUT_AW = 4
    JTAG_TIMEOUT_W = 5
    JTAG_TIMEOUT_B = 6
    JTAG_AXI_OKAY = 7
    JTAG_AXI_EXOKAY = 8
    JTAG_AXI_SLVERR = 9
    JTAG_AXI_DECERR = 10


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
        self.status = JTAGToAXIStatus(status & 0xF)  # 4 bits

    def get_jdr(self):
        """
        Packs the fields into an 36-bit register and returns the formatted value.
        | DATA_RD [(_AXI_ADDR_WIDTH+33-1):3] | STATUS [3:0] |
        """
        jdr = (self.data_rd << 4) | (self.status.value << 0)
        return jdr

    @classmethod
    def from_jdr(cls, jdr_value):
        """
        Takes an 36-bit value and decodes it into the class attributes.
        """
        data_rd_new = (jdr_value >> 4) & bits_to_ff_hex(_AXI_DATA_WIDTH)
        status_new = jdr_value & 0xF
        return cls(data_rd=data_rd_new, status=status_new)

    def __str__(self):
        return f"DATA RD: {hex(self.data_rd)}, STATUS: {self.status}"

    def __eq__(self, other):
        if isinstance(other, JDRStatusAXI):
            return self.data_rd == other.data_rd and self.status == other.status
        return False


class BaseJtagToAXI:
    @abstractmethod
    def __init__(
        self,
        addr_width: int = 32,
        data_width: int = 32,
        async_fifo_depth: int = 4,
        ic_reset_width: int = 4,
    ):
        """Initialize the interface (for hardware or DUT)."""
        self.addr_width = addr_width
        self.data_width = data_width
        self.ic_reset_width = ic_reset_width
        # Initialize JDR values
        self.idcode_jdr = 0
        self.ic_reset_jdr = 0
        self.addr_axi_jdr = 0
        self.data_write_axi_jdr = 0
        self.wstrb_axi_jdr = 0
        self.ctrl_axi_jdr = JDRCtrlAXI()
        self.status_axi_jdr = 0
        self.usercode_jdr = 0
        self.async_fifo_depth = async_fifo_depth
        self.tap_state = JTAGState.TEST_LOGIC_RESET

        # {current_state: {next_state: [TMS_sequence]}}
        self.state_transitions = {
            JTAGState.TEST_LOGIC_RESET: {
                JTAGState.RUN_TEST_IDLE: [0],
                JTAGState.SELECT_DR_SCAN: [1, 0],
            },
            JTAGState.RUN_TEST_IDLE: {
                JTAGState.SELECT_DR_SCAN: [1],
            },
            JTAGState.SELECT_DR_SCAN: {
                JTAGState.CAPTURE_DR: [0],
                JTAGState.SELECT_IR_SCAN: [1],
            },
            JTAGState.CAPTURE_DR: {
                JTAGState.SHIFT_DR: [0],
                JTAGState.EXIT1_DR: [1],
            },
            JTAGState.SHIFT_DR: {
                JTAGState.EXIT1_DR: [1],
            },
            JTAGState.EXIT1_DR: {
                JTAGState.UPDATE_DR: [1],
                JTAGState.PAUSE_DR: [0],
            },
            JTAGState.PAUSE_DR: {
                JTAGState.EXIT2_DR: [1],
            },
            JTAGState.EXIT2_DR: {
                JTAGState.SHIFT_DR: [0],
                JTAGState.UPDATE_DR: [1],
            },
            JTAGState.UPDATE_DR: {
                JTAGState.RUN_TEST_IDLE: [0],
                JTAGState.SELECT_DR_SCAN: [1],
            },
            JTAGState.SELECT_IR_SCAN: {
                JTAGState.CAPTURE_IR: [0],
                JTAGState.TEST_LOGIC_RESET: [1],
            },
            JTAGState.CAPTURE_IR: {
                JTAGState.SHIFT_IR: [0],
                JTAGState.EXIT1_IR: [1],
            },
            JTAGState.SHIFT_IR: {
                JTAGState.EXIT1_IR: [1],
            },
            JTAGState.EXIT1_IR: {
                JTAGState.UPDATE_IR: [1],
                JTAGState.PAUSE_IR: [0],
            },
            JTAGState.PAUSE_IR: {
                JTAGState.EXIT2_IR: [1],
            },
            JTAGState.EXIT2_IR: {
                JTAGState.SHIFT_IR: [0],
                JTAGState.UPDATE_IR: [1],
            },
            JTAGState.UPDATE_IR: {
                JTAGState.RUN_TEST_IDLE: [0],
                JTAGState.SELECT_DR_SCAN: [1],
            },
        }

    def _convert_size(self, value):
        """Convert byte size into asize."""
        for size in AXISize:
            if (2**size.value) == value:
                return size
        raise ValueError(f"No asize value found for {value} number of bytes")

    @abstractmethod
    def write_axi(self, addr, data, size):
        """Send data through JTAG."""
        pass

    @abstractmethod
    def read_axi(self, addr, size):
        """Read data from JTAG."""
        pass

    @abstractmethod
    def reset(self):
        """Reset the JTAG interface."""
        pass

    @abstractmethod
    def write_read_ic_reset(self):
        """Write IC Reset a value."""
        pass

    @abstractmethod
    def _get_idcode(self):
        """Get JTAG IDCODE."""
        pass
