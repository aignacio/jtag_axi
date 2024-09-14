#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_axi.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 15.09.2024
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
from jtag_axi.jtag_aux import reset_fsm, select_instruction, move_to_shift_dr, InstJTAG
from cocotb.triggers import ClockCycles, RisingEdge
from cocotb.clock import Clock
from cocotb.regression import TestFactory
from cocotb.result import TestFailure
from cocotb.runner import get_runner
from enum import Enum
from cocotbext.axi import AxiBus, AxiMaster, AxiRam


CLK_100MHz = (10, "ns")


def bin_list_to_num(binary_list):
    # Join the list into a string and convert to an integer using base 2
    binary_string = "".join(map(str, binary_list))
    return int(binary_string, 2)


def convert_to_bin_list(value, bits):
    # Convert the number to its binary representation and remove the '0b' prefix
    bin_str = bin(value & ((1 << bits) - 1))[2:].zfill(bits)
    # Convert the string representation of the binary number to a list of integers
    return [int(bit) for bit in bin_str]


@cocotb.test()
async def run_test(dut):
    await reset_fsm(dut)

    cocotb.start_soon(Clock(dut.clk_axi, *cfg.CLK_100MHz).start())

    axi_ram = AxiRam(AxiBus.from_entity(dut), dut.clk_axi, dut.ares_axi, size=2**32)

    await select_instruction(dut, InstJTAG.ADDR_AXI_REG)
    shifted_out = await move_to_shift_dr(dut, convert_to_bin_list(0x04, 32))
    await select_instruction(dut, InstJTAG.DATA_W_AXI_REG)
    shifted_out = await move_to_shift_dr(dut, convert_to_bin_list(0xDEADBEEF, 32))
    await select_instruction(dut, InstJTAG.CTRL_AXI_REG)
    shifted_out = await move_to_shift_dr(dut, convert_to_bin_list(0xC2, 8))
    await ClockCycles(dut.clk_axi, 100)

    await select_instruction(dut, InstJTAG.STATUS_AXI_REG)
    for _ in range(3):
        shifted_out = await move_to_shift_dr(dut, convert_to_bin_list(0x0, 35))

    await select_instruction(dut, InstJTAG.CTRL_AXI_REG)
    shifted_out = await move_to_shift_dr(dut, convert_to_bin_list(0x82, 8))
    await ClockCycles(dut.clk_axi, 100)

    await select_instruction(dut, InstJTAG.STATUS_AXI_REG)
    for _ in range(3):
        shifted_out = await move_to_shift_dr(dut, convert_to_bin_list(0xffffffff, 35))


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
        hdl_toplevel="jtag_axi_wrapper_tb",
        build_args=cfg.EXTRA_ARGS,
        #clean=True,
        timescale=cfg.TIMESCALE,
        waves=True,
        build_dir=SIM_BUILD,
    )

    runner.test(
        hdl_toplevel="jtag_axi_wrapper_tb", test_module=test_name, plusargs=cfg.PLUS_ARGS
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
            # (InstJTAG.STATUS_AXI_REG, 35, AccessMode.RO, 0x1fffffffff),
        # ],
    # )
    # factory.generate_tests()
