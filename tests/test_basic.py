#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_basic.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 23.08.2024
import random
import cocotb
import os
import logging
import pytest

from random import randrange
from const.const import cfg
from cocotb_test.simulator import run
from cocotb.triggers import ClockCycles
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.regression import TestFactory
from cocotb.result import TestFailure


async def setup_dut(dut, cycles):
    cocotb.start_soon(Clock(dut.clk, *cfg.CLK_100MHz).start())
    dut.arst.value = 1
    await ClockCycles(dut.clk, cycles)
    dut.arst.value = 0


@cocotb.test()
async def run_test(dut):
    await setup_dut(dut, cfg.RST_CYCLES)


def test_basic():
    """
    Basic test to check the DUT

    Test ID: 1
    """

    test_name = os.path.splitext(os.path.basename(__file__))[0]

    SIM_BUILD = os.path.join(
        cfg.TESTS_DIR, f"../../run_dir/sim_build_{cfg.SIMULATOR}_{test_name}"
    )

    run(
        python_search=[cfg.TESTS_DIR],
        includes=cfg.INC_DIR,
        verilog_sources=cfg.VERILOG_SOURCES,
        toplevel=cfg.TOPLEVEL,
        timescale=cfg.TIMESCALE,
        module=test_name,
        sim_build=SIM_BUILD,
        extra_args=cfg.EXTRA_ARGS,
        plus_args=cfg.PLUS_ARGS,
        waves=1,
    )
