#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_axi.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 14.09.2024
import cocotb
import os
import logging
import pytest
import random

import const.jtag
from pathlib import Path
from random import randrange
from const.const import cfg
from const.jtag import reset_fsm, select_instruction, move_to_shift_dr
from const.jtag import InstJTAG
from cocotb.triggers import RisingEdge
from cocotb.regression import TestFactory
from cocotb.result import TestFailure
from cocotb.runner import get_runner
from enum import Enum
from cocotbext.axi import AxiBus, AxiMaster, AxiRam

def gen_bin_list(length):
    if length < 0:
        raise ValueError("Length must be a non-negative integer.")
    # Generate a list of random 1s and 0s
    binary_list = [random.choice([0, 1]) for _ in range(length)]
    return binary_list


def bin_list_to_num(binary_list):
    # Join the list into a string and convert to an integer using base 2
    binary_string = "".join(map(str, binary_list))
    return int(binary_string, 2)


@cocotb.test()
async def run_test(dut):
    await reset_fsm(dut)


def test_axi():
    """
    Test to perform w/r operations through the JTAG 

    Test ID: 4
    """

    test_name = os.path.splitext(os.path.basename(__file__))[0]

    SIM_BUILD = os.path.join(
        cfg.TESTS_DIR, f"../../run_dir/{test_name}_{cfg.SIMULATOR}"
    )

    runner = get_runner(cfg.SIMULATOR)
    runner.build(
        includes=cfg.INC_DIR,
        verilog_sources=cfg.VERILOG_SOURCES,
        hdl_toplevel="jtag_axi_wrapper",
        build_args=cfg.EXTRA_ARGS,
        clean=True,
        timescale=cfg.TIMESCALE,
        waves=True,
        build_dir=SIM_BUILD,
    )

    runner.test(
        hdl_toplevel="jtag_axi_wrapper", test_module=test_name, plusargs=cfg.PLUS_ARGS
    )


# if cocotb.SIM_NAME:
    # factory = TestFactory(run_test)
    # factory.add_option(
        # "jtag_dr",
        # [
            # (InstJTAG.BYPASS, 1, AccessMode.RO, 0x1),
            # (InstJTAG.IC_RESET, 4, AccessMode.RW, 0xf),
            # (InstJTAG.IDCODE, 32, AccessMode.RO, 0xfff_ffff),
            # (InstJTAG.ADDR_AXI_REG, 32, AccessMode.RW, 0xffff_ffff),
            # (InstJTAG.DATA_W_AXI_REG, 32, AccessMode.RW, 0xffff_ffff),
            # (InstJTAG.CTRL_AXI_REG, 8, AccessMode.RW, 0xc7),
            # (InstJTAG.STATUS_AXI_REG, 37, AccessMode.RO, 0x1fffffffff),
        # ],
    # )
    # factory.generate_tests()
