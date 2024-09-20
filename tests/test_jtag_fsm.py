#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_jtag_fsm.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 20.09.2024
import cocotb
import logging
import pytest
import random
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
from random import randrange
from const.const import cfg
from jtag_axi.jtag_base import JTAGState
from cocotb.triggers import ClockCycles, Timer
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.regression import TestFactory
from cocotb.result import TestFailure
from cocotb.runner import get_runner


TestFailure.__test__ = False


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


def pick_random_value(input_list):
    if input_list:
        return random.choice(input_list)
    else:
        return None  # Return None if the list is empty


def get_tms():
    while True:
        yield pick_random_value([0, 1])

# JTAG FSM Model
class JTAGFSM:
    def __init__(self):
        self.state = JTAGState.TEST_LOGIC_RESET

    @property
    def fsm(self):
        return self.state

    def reset(self):
        self.state = JTAGState.TEST_LOGIC_RESET

    def transition(self, tms):
        if self.state == JTAGState.TEST_LOGIC_RESET:
            if tms == 0:
                self.state = JTAGState.RUN_TEST_IDLE
        elif self.state == JTAGState.RUN_TEST_IDLE:
            if tms == 1:
                self.state = JTAGState.SELECT_DR_SCAN
        elif self.state == JTAGState.SELECT_DR_SCAN:
            if tms == 0:
                self.state = JTAGState.CAPTURE_DR
            else:
                self.state = JTAGState.SELECT_IR_SCAN
        elif self.state == JTAGState.CAPTURE_DR:
            if tms == 0:
                self.state = JTAGState.SHIFT_DR
            else:
                self.state = JTAGState.EXIT1_DR
        elif self.state == JTAGState.SHIFT_DR:
            if tms == 1:
                self.state = JTAGState.EXIT1_DR
        elif self.state == JTAGState.EXIT1_DR:
            if tms == 0:
                self.state = JTAGState.PAUSE_DR
            else:
                self.state = JTAGState.UPDATE_DR
        elif self.state == JTAGState.PAUSE_DR:
            if tms == 1:
                self.state = JTAGState.EXIT2_DR
        elif self.state == JTAGState.EXIT2_DR:
            if tms == 0:
                self.state = JTAGState.SHIFT_DR
            else:
                self.state = JTAGState.UPDATE_DR
        elif self.state == JTAGState.UPDATE_DR:
            if tms == 0:
                self.state = JTAGState.RUN_TEST_IDLE
            else:
                self.state = JTAGState.SELECT_DR_SCAN
        elif self.state == JTAGState.SELECT_IR_SCAN:
            if tms == 0:
                self.state = JTAGState.CAPTURE_IR
            else:
                self.state = JTAGState.TEST_LOGIC_RESET
        elif self.state == JTAGState.CAPTURE_IR:
            if tms == 0:
                self.state = JTAGState.SHIFT_IR
            else:
                self.state = JTAGState.EXIT1_IR
        elif self.state == JTAGState.SHIFT_IR:
            if tms == 1:
                self.state = JTAGState.EXIT1_IR
        elif self.state == JTAGState.EXIT1_IR:
            if tms == 0:
                self.state = JTAGState.PAUSE_IR
            else:
                self.state = JTAGState.UPDATE_IR
        elif self.state == JTAGState.PAUSE_IR:
            if tms == 1:
                self.state = JTAGState.EXIT2_IR
        elif self.state == JTAGState.EXIT2_IR:
            if tms == 0:
                self.state = JTAGState.SHIFT_IR
            else:
                self.state = JTAGState.UPDATE_IR
        elif self.state == JTAGState.UPDATE_IR:
            if tms == 0:
                self.state = JTAGState.RUN_TEST_IDLE
            else:
                self.state = JTAGState.SELECT_DR_SCAN
        else:
            self.state = JTAGState.TEST_LOGIC_RESET


@cocotb.test()
async def run_test(dut):
    await reset_fsm(dut)
    n = 2000

    jtag_fsm = JTAGFSM()

    for i in range(n):
        tms = next(get_tms())
        dut.tms.value = tms
        jtag_fsm.transition(tms)
        await update_tck(dut)
        assert JTAGState(dut.fsm_ff.value) == jtag_fsm.fsm, "JTAG FSM diverges"


def test_jtag_fsm():
    """
    Check JTAG FSM transitions

    Test ID: 1
    """

    test_name = os.path.splitext(os.path.basename(__file__))[0]

    SIM_BUILD = os.path.join(
        cfg.TESTS_DIR, f"../../run_dir/{test_name}_{cfg.SIMULATOR}"
    )

    runner = get_runner(cfg.SIMULATOR)
    runner.build(
        includes=cfg.INC_DIR,
        verilog_sources=cfg.VERILOG_SOURCES,
        hdl_toplevel="jtag_axi_tap_ctrl_fsm",
        build_args=cfg.EXTRA_ARGS,
        clean=True,
        timescale=cfg.TIMESCALE,
        waves=True,
        build_dir=SIM_BUILD,
    )

    runner.test(
        hdl_toplevel="jtag_axi_tap_ctrl_fsm", test_module=test_name, plusargs=cfg.PLUS_ARGS
    )
