#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : jtag_axi.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
# Date              : 15.09.2024
# Last Modified Date: 16.09.2024
import os
from abc import abstractmethod
from .jtag_aux import JTAGState, InstJTAG
from cocotb.triggers import ClockCycles, Timer
from cocotb.handle import SimHandleBase


def bin_to_num(binary_list):
    # Join the list into a string and convert to an integer using base 2
    binary_string = "".join(map(str, binary_list))
    return int(binary_string, 2)


def bin_list(value, bits):
    # Convert the number to its binary representation and remove the '0b' prefix
    bin_str = bin(value & ((1 << bits) - 1))[2:].zfill(bits)
    # Convert the string representation of the binary number to a list of integers
    return [int(bit) for bit in bin_str]


class BaseJtagToAXI:
    @abstractmethod
    def __init__(self, addr_width: int = 32, data_width: int = 32):
        """Initialize the interface (for hardware or DUT)."""
        self.addr_width = addr_width
        self.data_width = data_width
        self.tap_state = JTAGState.TEST_LOGIC_RESET

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
        # Initialize JDR values
        self.ic_reset_jdr = 0
        self.addr_axi_jdr = 0
        self.data_write_axi_jdr = 0
        self.ctrl_axi_jdr = 0
        self.status_axi_jdr = 0

        super().__init__(**kwargs)

        # Define the state transition table:
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

    async def _set_tap_state(self, next_state):
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

    async def _set_ir(self, instr):
        await self._set_tap_state(JTAGState.SHIFT_IR)

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

        await self._set_tap_state(JTAGState.UPDATE_IR)
        tdo.append(self.dut.tdo.value)
        await self._set_tap_state(JTAGState.RUN_TEST_IDLE)
        return tdo[::-1]

    async def _set_dr(self, jdr_value, jdr_length):
        jdr_value = bin_list(jdr_value, jdr_length)
        await self._set_tap_state(JTAGState.SHIFT_DR)

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
        await self._set_tap_state(JTAGState.UPDATE_DR)
        await self._set_tap_state(JTAGState.RUN_TEST_IDLE)
        return tdo[::-1]

    async def _get_idcode(self):
        tdo = await self._set_ir(InstJTAG.IDCODE)
        tdo = await self._set_dr(0x00, 32)
        return bin_to_num(tdo)

    async def _set_jdr(self, jdr: InstJTAG, value: int):
        tdo = await self._set_ir(jdr)
        tdo = await self._set_dr(value, jdr.value[1])
        return bin_to_num(tdo)

    async def init_jdr(self):
        self.idcode = hex(await self._get_idcode())
        ic_reset = hex(await self._set_jdr(InstJTAG.IC_RESET, 0x00))
        self.ic_reset = 0x00
        self.dut.log.info("---------------------------------")
        self.dut.log.info("|=> JDR - JTAG Data Registers <=|")
        self.dut.log.info("---------------------------------")
        self.dut.log.info(f"- IDCODE     \t{self.idcode}")
        self.dut.log.info(f"- IC_RESET   \tWas: {ic_reset} \tNow: 0x00")

    async def _set_addr_axi(self, value: int):
        self.addr_axi = value
        await self._set_jdr(InstJTAG.ADDR_AXI_REG, value)

    async def _set_data_axi(self, value: int):
        self.data_axi = value
        await self._set_jdr(InstJTAG.DATA_W_AXI_REG, value)
