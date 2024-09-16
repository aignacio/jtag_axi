#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_ir.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 16.09.2024
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
from jtag_axi.jtag_aux import InstJTAG, reset_fsm, select_instruction
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.regression import TestFactory
from cocotb.result import TestFailure
from cocotb.runner import get_runner


TestFailure.__test__ = False


def rand_inst():
    return random.choice(list(InstJTAG))


@cocotb.test()
async def run_test(dut):
    await reset_fsm(dut)

    for _ in range(1000):
        inst = rand_inst()
        await select_instruction(dut, inst.value[0])
        assert (
            int(inst.value[0], 2) == dut.u_instruction_register.ir_ff.value
        ), "Instruction selected is wrong!"


def test_ir():
    """
    Check all available instructions through the IR

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
        hdl_toplevel="jtag_axi_tap_wrapper",
        build_args=cfg.EXTRA_ARGS,
        clean=True,
        timescale=cfg.TIMESCALE,
        waves=True,
        build_dir=SIM_BUILD,
    )

    runner.test(
        hdl_toplevel="jtag_axi_tap_wrapper", test_module=test_name, plusargs=cfg.PLUS_ARGS
    )
