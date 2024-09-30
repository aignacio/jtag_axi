#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : jtag_axi_sim.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
# Date              : 15.09.2024
# Last Modified Date: 30.09.2024
import os
from .jtag_base import *
from cocotb.triggers import ClockCycles, Timer
from cocotb.handle import SimHandleBase
from enum import Enum


def bin_to_num(binary_list):
    # Join the list into a string and convert to an integer using base 2
    binary_string = "".join(map(str, binary_list))
    return int(binary_string, 2)


def bin_list(value, bits):
    # Convert the number to its binary representation and remove the '0b' prefix
    bin_str = bin(value & ((1 << bits) - 1))[2:].zfill(bits)
    # Convert the string representation of the binary number to a list of integers
    return [int(bit) for bit in bin_str]


class SimJtagToAXI(BaseJtagToAXI):
    def __init__(
        self,
        dut: SimHandleBase = None,
        freq: int = 1e6,
        name: str = "JTAG to AXI IP",
        **kwargs,
    ):
        """Initialize the DUT JTAG interface."""
        self.dut = dut
        self.freq_period = (1 / freq) * 1e9

        super().__init__(**kwargs)

        dut.log.info("------------------------------")
        dut.log.info("|=> JTAG Interface created <=|")
        dut.log.info("------------------------------")
        dut.log.info(f"- Address width\t{self.addr_width}")
        dut.log.info(f"- Data width   \t{self.data_width}")
        if freq >= 1e6:
            dut.log.info(f"- Frequency    \t{freq/1e6:.3f} MHz")
        elif freq >= 1e3:
            dut.log.info(f"- Frequency    \t{freq/1e3:.3f} kHz")
        else:
            dut.log.info(f"- Frequency    \t{freq:.3f} Hz")

    async def reset(self):
        self.dut.trstn.value = 0
        await Timer(self.freq_period / 2, units="ns")
        self.dut.trstn.value = 1
        await Timer(self.freq_period / 2, units="ns")

    def _find_tap_path(self, current_state, target_state, visited=None):
        """
        Recursively finds a path and the TMS sequence from the current state
        to the target state. Tracks visited states to avoid infinite loops.
        """

        # Initialize the visited states set if not provided
        if visited is None:
            visited = set()

        # Add the current state to the visited set
        visited.add(current_state)

        # Base case: if already in the target state, no transition needed
        if current_state == target_state:
            return []

        # Depth-First Search (DFS) to find a valid path to the target state
        for next_state, tms_sequence in self.state_transitions.get(
            current_state, {}
        ).items():
            if next_state == target_state:
                return tms_sequence

            # Continue searching if the next state has not been visited
            if next_state not in visited:
                sub_path = self._find_tap_path(next_state, target_state, visited)
                if sub_path is not None:
                    return tms_sequence + sub_path

        # No valid path found
        return None

    async def _update_tck(self):
        self.dut.tck.value = 0
        await Timer(self.freq_period / 2, units="ns")
        self.dut.tck.value = 1
        await Timer(self.freq_period / 2, units="ns")

    async def _shift_tap_state(self, next_state):
        """
        Sets the TAP controller state to the desired next state by calculating
        the appropriate TMS sequence. If the transition is not directly possible,
        finds the shortest path through valid states.
        """
        # Get the current state
        current_state = self.tap_state

        # Find the path from the current state to the next state
        tms_sequence = self._find_tap_path(current_state, next_state)

        if tms_sequence is not None:
            # Set the new TAP state
            self.tap_state = next_state
        else:
            raise ValueError(
                f"Cannot find a valid state transition from {current_state} to {next_state}"
            )

        for tms in tms_sequence:
            self.dut.tms.value = tms
            await self._update_tck()

    async def _shift_ir(self, instr):
        await self._shift_tap_state(JTAGState.SHIFT_IR)

        tdo = []
        for idx, tdi_val in enumerate(instr.value[0][2:][::-1]):
            self.dut.tdi.value = int(tdi_val)
            if idx == len(instr.value[0][2:]) - 1:
                break
            self.dut.tck.value = 0
            await Timer(self.freq_period / 2, units="ns")
            tdo.append(self.dut.tdo.value)
            self.dut.tck.value = 1
            await Timer(self.freq_period / 2, units="ns")

        await self._shift_tap_state(JTAGState.UPDATE_IR)
        tdo.append(self.dut.tdo.value)
        await self._shift_tap_state(JTAGState.RUN_TEST_IDLE)
        return tdo[::-1]

    async def _shift_dr(self, jdr_value, jdr_length):
        jdr_value = bin_list(jdr_value, jdr_length)
        await self._shift_tap_state(JTAGState.SHIFT_DR)

        tdo = []
        for idx, tdi_val in enumerate(jdr_value[::-1]):
            self.dut.tdi.value = int(tdi_val)
            if idx == len(jdr_value) - 1:
                break
            self.dut.tck.value = 0
            await Timer(self.freq_period / 2, units="ns")
            tdo.append(self.dut.tdo.value)
            self.dut.tck.value = 1
            await Timer(self.freq_period / 2, units="ns")

        self.dut.tms.value = 1
        self.dut.tck.value = 0
        await Timer(self.freq_period / 2, units="ns")
        tdo.append(self.dut.tdo.value)
        self.dut.tck.value = 1
        await Timer(self.freq_period / 2, units="ns")
        self.tap_state = JTAGState.EXIT1_DR
        await self._shift_tap_state(JTAGState.UPDATE_DR)
        await self._shift_tap_state(JTAGState.RUN_TEST_IDLE)
        return tdo[::-1]

    async def _get_idcode(self):
        tdo = await self._shift_ir(InstJTAG.IDCODE)
        tdo = await self._shift_dr(0x00, 32)
        return bin_to_num(tdo)

    async def _shift_jdr(self, jdr: InstJTAG, value: int):
        tdo = await self._shift_ir(jdr)
        tdo = await self._shift_dr(value, jdr.value[1])
        return bin_to_num(tdo)

    async def _get_jdr(self, jdr: InstJTAG):
        tdo = await self._shift_ir(jdr)
        old = bin_to_num(await self._shift_dr(0x00, jdr.value[1]))
        tdo = await self._shift_dr(old, jdr.value[1])
        return old

    async def read_jdrs(self):
        self.idcode_jdr = hex(await self._get_idcode())
        self.ic_reset_jdr = hex(await self._get_jdr(InstJTAG.IC_RESET))
        self.addr_axi_jdr = hex(await self._get_jdr(InstJTAG.ADDR_AXI_REG))
        self.data_write_axi_jdr = hex(await self._get_jdr(InstJTAG.DATA_W_AXI_REG))
        self.status_axi_jdr = hex(await self._get_jdr(InstJTAG.STATUS_AXI_REG))
        self.ctrl_axi_jdr = hex(await self._get_jdr(InstJTAG.CTRL_AXI_REG))
        self.wstrb_axi_jdr = hex(await self._get_jdr(InstJTAG.WSTRB_AXI_REG))
        self.usercode_jdr = hex(await self._get_jdr(InstJTAG.USERCODE))

        self.dut.log.info("---------------------------------")
        self.dut.log.info("|=> JDR - JTAG Data Registers <=|")
        self.dut.log.info("---------------------------------")
        self.dut.log.info(f"- IDCODE     \t{self.idcode_jdr}")
        self.dut.log.info(f"- IC_RESET   \t{self.ic_reset_jdr}")
        self.dut.log.info(f"- ADDR_AXI   \t{self.addr_axi_jdr}")
        self.dut.log.info(f"- DATA_AXI   \t{self.data_write_axi_jdr}")
        self.dut.log.info(f"- CTRL_AXI   \t{self.ctrl_axi_jdr}")
        self.dut.log.info(f"- WSTRB_AXI  \t{self.wstrb_axi_jdr}")
        self.dut.log.info(f"- USERCODE   \t{self.usercode_jdr}")

    async def _shift_addr_axi(self, value: int):
        self.addr_axi_jdr = value
        tdo = await self._shift_jdr(InstJTAG.ADDR_AXI_REG, value)
        return tdo

    async def _shift_data_axi(self, value: int):
        self.data_write_axi_jdr = value
        tdo = await self._shift_jdr(InstJTAG.DATA_W_AXI_REG, value)
        return tdo

    async def _shift_wstrb_axi(self, value: int):
        self.wstrb_axi_jdr = value
        tdo = await self._shift_jdr(InstJTAG.WSTRB_AXI_REG, value)
        return tdo

    async def _shift_ctrl_axi(self, value: JDRCtrlAXI):
        self.ctrl_axi_jdr = value
        tdo = await self._shift_jdr(InstJTAG.CTRL_AXI_REG, value.get_jdr())
        return tdo

    async def _shift_status_axi(self, value: JDRStatusAXI):
        self.status_axi_jdr = value
        tdo = await self._shift_jdr(InstJTAG.STATUS_AXI_REG, value.get_jdr())
        return tdo

    async def write_axi(self, address, data, size, wstrb=0xF):
        if self.addr_axi_jdr != address:
            if address < 2**self.addr_width:
                await self._shift_addr_axi(address)
            else:
                raise ValueError(
                    "Address exceeds max of address width {self.addr_width}"
                )
        else:
            self.dut._log.debug("Skipping address shift due to value match")

        if self.data_write_axi_jdr != data:
            if data < 2**self.data_width:
                await self._shift_data_axi(data)
            else:
                raise ValueError(
                    "Data write exceeds max of data width {self.data_width}"
                )
        else:
            self.dut._log.debug("Skipping data shift due to value match")

        if self.wstrb_axi_jdr != wstrb:
            await self._shift_wstrb_axi(wstrb)
        else:
            self.dut._log.debug("Skipping data shift due to value match")

        empty_ctrl = JDRCtrlAXI(start=0)
        send_write = JDRCtrlAXI(
            start=1, txn_type=TxnType.AXI_WRITE, size_axi=self._convert_size(size)
        )
        current = JDRCtrlAXI.from_jdr(await self._shift_ctrl_axi(empty_ctrl))

        # Check whether we have enough free slots to send
        while current.fifo_ocup >= 4:
            await self._shift_status_axi(JDRStatusAXI())
            current = JDRCtrlAXI.from_jdr(await self._shift_ctrl_axi(empty_ctrl))

        # Send the TXN
        current = JDRCtrlAXI.from_jdr(await self._shift_ctrl_axi(send_write))
        self.dut.log.info(
            f"[JTAG to AXI][WRITE] Addr = {hex(address)} / Data = {hex(data)}"
            f" Size = {self._convert_size(size)} / WrStrb = {bin(wstrb)}"
        )
        status_axi = JDRStatusAXI.from_jdr(await self._shift_status_axi(JDRStatusAXI()))
        while status_axi.status == JTAGToAXIStatus.JTAG_RUNNING:
            status_axi = JDRStatusAXI.from_jdr(
                await self._shift_status_axi(JDRStatusAXI())
            )
        return status_axi

    async def read_axi(self, address, size):
        if self.addr_axi_jdr != address:
            if address < 2**self.addr_width:
                await self._shift_addr_axi(address)
            else:
                raise ValueError(
                    "Address exceeds max of address width {self.addr_width}"
                )
        else:
            self.dut._log.debug("Skipping address shift due to value match")

        empty_ctrl = JDRCtrlAXI(start=0)
        send_write = JDRCtrlAXI(
            start=1, txn_type=TxnType.AXI_READ, size_axi=self._convert_size(size)
        )
        current = JDRCtrlAXI.from_jdr(await self._shift_ctrl_axi(empty_ctrl))

        # Check whether we have enough free slots to send
        while current.fifo_ocup >= 4:
            await self._shift_status_axi(JDRStatusAXI())
            current = JDRCtrlAXI.from_jdr(await self._shift_ctrl_axi(empty_ctrl))

        # Send the TXN
        current = JDRCtrlAXI.from_jdr(await self._shift_ctrl_axi(send_write))
        self.dut.log.info(
            f"[JTAG to AXI][READ] Addr = {hex(address)} / Size = {self._convert_size(size)}"
        )

        status_axi = JDRStatusAXI.from_jdr(await self._shift_status_axi(JDRStatusAXI()))
        while status_axi.status == JTAGToAXIStatus.JTAG_RUNNING:
            status_axi = JDRStatusAXI.from_jdr(
                await self._shift_status_axi(JDRStatusAXI())
            )
        return status_axi
