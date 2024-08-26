#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_ir.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 26.08.2024
import cocotb
import os
import logging
import pytest
import random

from pathlib import Path
from random import randrange
from const.const import cfg
from const.jtag import JTAGFSM, JTAGState, jtag_transitions
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
    """
    Moves the DUT JTAG TAP controller to the specified state.

    :param dut: The device under test (DUT)
    :param state: The target JTAG state (of type JTAGState)
    """
    tck = dut.tck  # JTAG clock
    tms = dut.tms  # JTAG mode select
    tdi = dut.tdi  # JTAG data in (if needed)

    transitions = jtag_transitions[state]

    for tms_value in transitions:
        dut.tms.value = tms_value
        await update_tck(dut)


@cocotb.test()
async def run_test(dut):
    await reset_fsm(dut)

    jtag_fsm = JTAGFSM()

    await move_to_jtag_state(dut, JTAGState.SHIFT_IR)


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
