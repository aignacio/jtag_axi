#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : jtag_axi_hw.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
# Date              : 15.09.2024
# Last Modified Date: 30.09.2024
import os
from .jtag_base import *
from enum import Enum
from pyftdi.jtag import JtagEngine, JtagTool
from pyftdi.ftdi import Ftdi
from os import environ
from pyftdi.bits import BitSequence


def bin_to_num(binary_list):
    # Join the list into a string and convert to an integer using base 2
    binary_string = "".join(map(str, binary_list))
    return int(binary_string, 2)


def bin_list(value, bits):
    # Convert the number to its binary representation and remove the '0b' prefix
    bin_str = bin(value & ((1 << bits) - 1))[2:].zfill(bits)
    # Convert the string representation of the binary number to a list of integers
    return [int(bit) for bit in bin_str]


class JtagToAXIFTDI(BaseJtagToAXI):
    def __init__(
        self,
        device="ftdi://ftdi:2232/1",
        name: str = "JTAG to AXI IP",
        freq: int = 1e6,
        trst: bool = False,
        debug: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.ftdi = Ftdi()
        self.ftdi.open_from_url(device)

        self.jtag = JtagEngine(trst=trst, frequency=freq)
        self.jtag.configure(environ.get("FTDI_DEVICE", device))
        self.jtag.reset()

        self.tool = JtagTool(self.jtag)
        self.debug = debug
        if self.debug:
            print(f"[JTAG_to_AXI] ---- Init Device ----")
            print(f"[JTAG_to_AXI] Init device \t{device}")
            if freq >= 1e6:
                print(f"[JTAG_to_AXI] Frequency \t{freq/1e6:.3f} MHz")
            elif freq >= 1e3:
                print(f"[JTAG_to_AXI] Frequency \t{freq/1e3:.3f} kHz")
            else:
                print(f"[JTAG_to_AXI] Frequency \t{freq:.3f} Hz")
            print(f"[JTAG_to_AXI] IDCODE    \t{hex(self._get_jdr(InstJTAG.IDCODE))}")
            print(f"[JTAG_to_AXI] AXI Address width\t{self.addr_width}")
            print(f"[JTAG_to_AXI] AXI Data width  \t{self.data_width}")
            print(f"[JTAG_to_AXI] AFIFO Depth  \t{self.async_fifo_depth}")
            print(f"[JTAG_to_AXI] IC Reset width  \t{self.ic_reset_width}")

        self.idcode_jdr = self._get_jdr(InstJTAG.IDCODE)
        self.ic_reset_jdr = self._get_jdr(InstJTAG.IC_RESET)
        self.addr_axi_jdr = self._get_jdr(InstJTAG.ADDR_AXI_REG)
        self.data_write_axi_jdr = self._get_jdr(InstJTAG.DATA_W_AXI_REG)
        self.status_axi_jdr = self._get_jdr(InstJTAG.STATUS_AXI_REG)
        self.ctrl_axi_jdr = self._get_jdr(InstJTAG.CTRL_AXI_REG)
        self.wstrb_axi_jdr = self._get_jdr(InstJTAG.WSTRB_AXI_REG)

    def reset(self):
        """Reset the JTAG interface."""
        if self.debug:
            print(f"[JTAG_to_AXI] Reset issued")
        self.jtag.reset()

    def _get_jdr(self, jdr: InstJTAG):
        instruction = BitSequence(jdr.value[0][2:], msb=True, length=4)
        self.jtag.change_state("shift_ir")
        retval = self.jtag.shift_and_update_register(instruction)
        self.jtag.go_idle()
        self.jtag.change_state("shift_dr")
        jdr_value = self.jtag.shift_and_update_register(BitSequence("0" * jdr.value[1]))
        # Shift back the old value that we replaced with 0s
        self.jtag.change_state("shift_dr")
        jdr_value_new = self.jtag.shift_and_update_register(jdr_value)
        self.jtag.go_idle()
        return int(jdr_value)

    def read_jdrs(self):
        self.idcode_jdr = self._get_jdr(InstJTAG.IDCODE)
        self.usercode_jdr = self._get_jdr(InstJTAG.USERCODE)
        self.ic_reset_jdr = self._get_jdr(InstJTAG.IC_RESET)
        self.addr_axi_jdr = self._get_jdr(InstJTAG.ADDR_AXI_REG)
        self.data_write_axi_jdr = self._get_jdr(InstJTAG.DATA_W_AXI_REG)
        self.status_axi_jdr = self._get_jdr(InstJTAG.STATUS_AXI_REG)
        self.ctrl_axi_jdr = self._get_jdr(InstJTAG.CTRL_AXI_REG)
        self.wstrb_axi_jdr = self._get_jdr(InstJTAG.WSTRB_AXI_REG)

        print(f"\n[JTAG_to_AXI] ---- Print JDRs ----")
        print(f"[JTAG_to_AXI] IDCODE     \t{hex(self.idcode_jdr)}")
        print(f"[JTAG_to_AXI] USERCODE   \t{hex(self.usercode_jdr)}")
        print(f"[JTAG_to_AXI] IC_RESET   \t{hex(self.ic_reset_jdr)}")
        print(f"[JTAG_to_AXI] ADDR_AXI   \t{hex(self.addr_axi_jdr)}")
        print(f"[JTAG_to_AXI] DATA_AXI   \t{hex(self.data_write_axi_jdr)}")
        print(f"[JTAG_to_AXI] CTRL_AXI   \t{hex(self.ctrl_axi_jdr)}")
        print(f"[JTAG_to_AXI] WSTRB_AXI  \t{hex(self.wstrb_axi_jdr)}")

    def _shift_jdr(self, jdr: InstJTAG, val: int):
        if self.debug:
            print(f"[JTAG_to_AXI] ---- Shift JDR ----")
        instruction = BitSequence(jdr.value[0][2:], msb=True, length=4)
        if self.debug:
            print(f"[JTAG_to_AXI] Updating JDR: {jdr.name} / Value: {val} ({hex(val)})")
        self.jtag.change_state("shift_ir")
        retval = self.jtag.shift_and_update_register(instruction)
        # self.jtag.go_idle()
        jdr_value = BitSequence(val, msb=False, length=jdr.value[1])
        self.jtag.change_state("shift_dr")
        jdr_value = self.jtag.shift_and_update_register(jdr_value)
        return int(jdr_value)

    def _update_current(self, info, current, new):
        if current == new:
            if self.debug:
                print(f"[JTAG_to_AXI] Skipping {info} shift due to value match")
            return False
        else:
            return True

    def write_axi(self, address, data, size=None, wstrb=0xF):
        if size is None:
            size = self.data_width // 8

        if address >= 2**self.addr_width:
            raise ValueError(
                f"[JTAG_to_AXI] Address exceeds max of address width {self.addr_width}"
            )

        if data >= 2**self.data_width:
            raise ValueError(
                f"[JTAG_to_AXI] Data write exceeds max of data width {self.data_width}"
            )

        if wstrb > int("1" * (self.data_width // 8), 2):
            raise ValueError(
                f"[JTAG_to_AXI] Write strobe exceeds max of {hex(int('1'*(self.data_width//8),2))}"
            )

        if size > (self.data_width // 8):
            raise ValueError(
                f"[JTAG_to_AXI] Number of bytes requested ({self.size}) is greater"
                f" than max ({self.data_width // 8})"
            )

        if self._update_current("address", self.addr_axi_jdr, address):
            self._shift_jdr(InstJTAG.ADDR_AXI_REG, address)
            self.addr_axi_jdr = address

        if self._update_current("write data", self.data_write_axi_jdr, data):
            self._shift_jdr(InstJTAG.DATA_W_AXI_REG, data)
            self.data_write_axi_jdr = data

        if self._update_current("write strobe", self.wstrb_axi_jdr, wstrb):
            self._shift_jdr(InstJTAG.WSTRB_AXI_REG, wstrb)
            self.wstrb_axi_jdr = wstrb

        empty_ctrl = JDRCtrlAXI(start=0).get_jdr()
        send_write = JDRCtrlAXI(
            start=1, txn_type=TxnType.AXI_WRITE, size_axi=self._convert_size(size)
        )
        current = JDRCtrlAXI.from_jdr(
            self._shift_jdr(InstJTAG.CTRL_AXI_REG, empty_ctrl)
        )

        # Check whether we have enough free slots to send
        while current.fifo_ocup >= self.async_fifo_depth:
            if self.debug:
                print(
                    f"[JTAG_to_AXI] Waiting ASYNC FIFO to have slots "
                    f"available, ocup: {current.fifo_ocup} / {self.async_fifo_depth}"
                )
            self._shift_jdr(InstJTAG.STATUS_AXI_REG, 0)
            current = JDRCtrlAXI.from_jdr(
                self._shift_jdr(InstJTAG.CTRL_AXI_REG, empty_ctrl)
            )

        # Send the TXN
        current = JDRCtrlAXI.from_jdr(
            self._shift_jdr(InstJTAG.CTRL_AXI_REG, send_write.get_jdr())
        )
        print(
            f"[JTAG_to_AXI][WRITE] Addr = {hex(address)} / Data = {hex(data)}"
            f" / Size = {self._convert_size(size)} / WrStrb = {bin(wstrb)}"
        )
        current = JDRCtrlAXI.from_jdr(
            self._shift_jdr(InstJTAG.CTRL_AXI_REG, empty_ctrl)
        )
        if self.debug:
            print(
                f"[JTAG_to_AXI] Current AFIFO size: {current.fifo_ocup} / {self.async_fifo_depth}"
            )
        status_axi = JDRStatusAXI.from_jdr(self._shift_jdr(InstJTAG.STATUS_AXI_REG, 0))
        while status_axi.status == JTAGToAXIStatus.JTAG_RUNNING:
            if self.debug:
                print(f"[JTAG_to_AXI] Waiting TXN to complete: " f"{status_axi.status}")
            status_axi = JDRStatusAXI.from_jdr(
                self._shift_jdr(InstJTAG.STATUS_AXI_REG, 0)
            )
        return status_axi

    def read_axi(self, address, size=None):
        if size is None:
            size = self.data_width // 8

        if address >= 2**self.addr_width:
            raise ValueError(
                f"[JTAG_to_AXI] Address exceeds max of address width {self.addr_width}"
            )

        if size > (self.data_width // 8):
            raise ValueError(
                f"[JTAG_to_AXI] Number of bytes requested ({self.size}) is greater"
                f" than max ({self.data_width // 8})"
            )

        if self._update_current("address", self.addr_axi_jdr, address):
            self._shift_jdr(InstJTAG.ADDR_AXI_REG, address)
            self.addr_axi_jdr = address

        empty_ctrl = JDRCtrlAXI(start=0).get_jdr()
        send_write = JDRCtrlAXI(
            start=1, txn_type=TxnType.AXI_READ, size_axi=self._convert_size(size)
        )
        current = JDRCtrlAXI.from_jdr(
            self._shift_jdr(InstJTAG.CTRL_AXI_REG, empty_ctrl)
        )

        # Check whether we have enough free slots to send
        while current.fifo_ocup >= self.async_fifo_depth:
            if self.debug:
                print(
                    f"[JTAG_to_AXI] Waiting ASYNC FIFO to have slots "
                    f"available, ocup: {current.fifo_ocup} / {self.async_fifo_depth}"
                )
            self._shift_jdr(InstJTAG.STATUS_AXI_REG, 0)
            current = JDRCtrlAXI.from_jdr(
                self._shift_jdr(InstJTAG.CTRL_AXI_REG, empty_ctrl)
            )

        # Send the TXN
        current = JDRCtrlAXI.from_jdr(
            self._shift_jdr(InstJTAG.CTRL_AXI_REG, send_write.get_jdr())
        )
        print(
            f"[JTAG_to_AXI][READ] Addr = {hex(address)}"
            f" / Size = {self._convert_size(size)}"
        )
        current = JDRCtrlAXI.from_jdr(
            self._shift_jdr(InstJTAG.CTRL_AXI_REG, empty_ctrl)
        )
        if self.debug:
            print(
                f"[JTAG_to_AXI] Current AFIFO size: {current.fifo_ocup} / {self.async_fifo_depth}"
            )
        status_axi = JDRStatusAXI.from_jdr(self._shift_jdr(InstJTAG.STATUS_AXI_REG, 0))
        while status_axi.status == JTAGToAXIStatus.JTAG_RUNNING:
            if self.debug:
                print(f"[JTAG_to_AXI] Waiting TXN to complete: {status_axi.status}")
            status_axi = JDRStatusAXI.from_jdr(
                self._shift_jdr(InstJTAG.STATUS_AXI_REG, 0)
            )
        return status_axi

    def write_ic_reset(self, value):
        if value >= 2**self.ic_reset_width:
            raise ValueError(
                f"[JTAG_to_AXI] Value to write on IC_RESET ({value}) is greater than max {2**self.ic_reset_width}"
            )
        if self.debug:
            print(f"[JTAG_to_AXI] Writing {value} in IC_RESET JDR")
        self._shift_jdr(InstJTAG.IC_RESET, value)
        self.ic_reset_jdr = value
