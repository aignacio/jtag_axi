#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : help_fn.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
# Date              : 15.09.2024
# Last Modified Date: 20.09.2024
from enum import Enum
import os
import sys
from cocotb.triggers import ClockCycles, Timer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from jtag_axi.jtag_base import JTAGState


# JTAG State Transitions - From TEST_LOGIC_RESET
JtagTrans = {
    JTAGState.TEST_LOGIC_RESET: [1, 1, 1, 1, 1],  # From any state
    JTAGState.RUN_TEST_IDLE: [0],  # From TEST_LOGIC_RESET  or other states
    JTAGState.SELECT_DR_SCAN: [0, 1],  # From RUN_TEST_IDLE
    JTAGState.CAPTURE_DR: [0, 1, 0],  # From SELECT_DR_SCAN
    JTAGState.SHIFT_DR: [0, 1, 0, 0],  # From CAPTURE_DR
    JTAGState.EXIT1_DR: [0, 1, 0, 1],  # From SHIFT_DR
    JTAGState.PAUSE_DR: [0, 1, 0, 1, 0],  # From EXIT1_DR
    JTAGState.EXIT2_DR: [0, 1, 0, 1, 0, 1],  # From PAUSE_DR
    JTAGState.UPDATE_DR: [0, 1, 0, 0, 1, 0, 1, 1],  # From EXIT2_DR or SHIFT_DR
    JTAGState.SELECT_IR_SCAN: [0, 1, 1, 0],  # From SELECT_DR_SCAN
    JTAGState.CAPTURE_IR: [0, 1, 1, 0],  # From SELECT_IR_SCAN
    JTAGState.SHIFT_IR: [0, 1, 1, 0, 0],  # From CAPTURE_IR
    JTAGState.EXIT1_IR: [0, 1, 1, 0, 1],  # From SHIFT_IR
    JTAGState.PAUSE_IR: [0, 1, 1, 0, 1, 0],  # From EXIT1_IR
    JTAGState.EXIT2_IR: [0, 1, 1, 0, 1, 0, 1],  # From PAUSE_IR
    JTAGState.UPDATE_IR: [0, 1, 1, 0, 1, 1],  # From EXIT2_IR or SHIFT_IR
}

async def reset_fsm(dut):
    dut.log.info(f"Reset JTAG FSM")
    dut.trstn.value = 0
    dut.tms.value = 0
    dut.tdi.value = 0
    dut.tck.value = 0
    await Timer(100, units="ns")
    dut.trstn.value = 1
    await Timer(50, units="ns")


async def update_tck(dut):
    dut.tck.value = 0
    await Timer(100, units="ns")
    dut.tck.value = 1
    await Timer(100, units="ns")


async def move_to_jtag_state(dut, state):
    tms = dut.tms

    transitions = JtagTrans[state]

    for _ in range(5):
        dut.tms.value = 0
        await update_tck(dut)

    #await reset_fsm(dut)

    for tms_value in transitions:
        dut.tms.value = tms_value
        await update_tck(dut)


async def select_instruction(dut, instr):
    dut.log.info(f"Setting up instr: {instr}")
    await move_to_jtag_state(dut, JTAGState.SHIFT_IR)

    for idx, tdi_val in enumerate(instr[2:][::-1]):
        dut.tdi.value = int(tdi_val)
        if idx == len(instr[2:]) - 1:
            break
        await update_tck(dut)

    dut.tms.value = 1
    await update_tck(dut)
    await update_tck(dut)
    dut.tms.value = 0
    await update_tck(dut)


async def move_to_shift_dr(dut, value):
    dut.log.info(f"Moving to shift DR")

    # Assuming we're on RUN_TEST_IDLE
    dut.tdi.value = 0
    dut.tms.value = 1
    await update_tck(dut)
    dut.tms.value = 0
    await update_tck(dut)
    dut.tms.value = 0
    await update_tck(dut)

    tdo = []
    for idx, tdi_val in enumerate(value[::-1]):
        dut.tdi.value = tdi_val

        if idx == len(value) - 1:
            break

        dut.tck.value = 0
        await Timer(100, units="ns")
        tdo.append(dut.tdo.value)
        dut.tck.value = 1
        await Timer(100, units="ns")

    dut.tms.value = 1

    dut.tck.value = 0
    await Timer(100, units="ns")
    tdo.append(dut.tdo.value)
    dut.tck.value = 1
    await Timer(100, units="ns")
    await update_tck(dut)
    dut.tms.value = 0
    await update_tck(dut)

    return tdo[::-1]
