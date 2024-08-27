#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_ir.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 27.08.2024
import cocotb
import os
import logging
import pytest
import random

from pathlib import Path
from random import randrange
from const.const import cfg
from const.jtag import JTAGFSM, JTAGState, jtag_trans, InstJTAG
from cocotb.triggers import ClockCycles, Timer
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.regression import TestFactory
from cocotb.result import TestFailure
from cocotb.runner import get_runner


async def reset_fsm(dut):
    dut._log.info(f"Resetting JTAG FSM")
    dut.trstn.value = 0
    dut.tms.value = 0
    dut.tdi.value = 0
    dut.tck.value = 0
    await Timer(10, units="ns")
    dut.trstn.value = 1
    await Timer(2, units="ns")


async def update_tck(dut):
    dut.tck.value = 0
    await Timer(1, units="ns")
    dut.tck.value = 1
    await Timer(1, units="ns")


async def move_to_jtag_state(dut, state):
    tms = dut.tms

    transitions = jtag_trans[state]

    await reset_fsm(dut)

    for tms_value in transitions:
        dut.tms.value = tms_value
        await update_tck(dut)


async def select_instruction(dut, instr):
    await move_to_jtag_state(dut, JTAGState.SHIFT_IR)

    for idx, tdi_val in enumerate(instr.value[2:][::-1]):
        dut.tdi.value = int(tdi_val)
        if idx == len(instr.value[2:]) - 1:
            break
        await update_tck(dut)

    dut.tms.value = 1
    await update_tck(dut)
    await update_tck(dut)
    dut.tms.value = 0
    await update_tck(dut)


def rand_inst():
    return random.choice(list(InstJTAG))


@cocotb.test()
async def run_test(dut):
    await reset_fsm(dut)

    for _ in range(1000):
        inst = rand_inst()
        await select_instruction(dut, inst)
        assert (
            int(inst.value, 2) == dut.u_ir.ir_ff.value
        ), "Instruction selected is wrong!"


def test_jtag_fsm():
    """
    Check all available instruction through the IR

    Test ID: 2
    """

    test_name = os.path.splitext(os.path.basename(__file__))[0]

    SIM_BUILD = os.path.join(
        cfg.TESTS_DIR, f"../../run_dir/{test_name}_{cfg.SIMULATOR}"
    )

    runner = get_runner(cfg.SIMULATOR)
    runner.build(
        includes=cfg.INC_DIR,
        verilog_sources=cfg.VERILOG_SOURCES,
        hdl_toplevel="jtag_wrapper",
        build_args=cfg.EXTRA_ARGS,
        clean=True,
        timescale=cfg.TIMESCALE,
        waves=True,
        build_dir=SIM_BUILD,
    )

    runner.test(
        hdl_toplevel="jtag_wrapper", test_module=test_name, plusargs=cfg.PLUS_ARGS
    )


if __name__ == "__main__":
    test_basic()
