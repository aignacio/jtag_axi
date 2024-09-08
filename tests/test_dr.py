#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_dr.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 08.09.2024
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


class JTAGDataRegister:
    ir_ins: InstJTAG.BYPASS
    shift_length: 1
    read_only: True


class JTAGDataRegister:
    def __init__(self, dut, ir_ins, shift_length, read_only):
        self.dut = dut
        self.ir_ins = ir_ins
        self.shift_length = shift_length
        self.read_only = read_only

    def display(self):
        self.dut.log.info("------------------------------")
        self.dut.log.info(f"IR Instruction: {self.ir_ins}")
        self.dut.log.info(f"Shift Length: {self.shift_length}")
        self.dut.log.info(f"Read Only: {self.read_only}")


@cocotb.test()
async def run_test(dut, jtag_dr=(InstJTAG.BYPASS, 1, True)):
    await reset_fsm(dut)
    args = (dut,) + jtag_dr
    dr = JTAGDataRegister(*args)
    dr.display()
    await select_instruction(dut, dr.ir_ins)
    shifted_in = gen_bin_list(dr.shift_length)
    shifted_out = await move_to_shift_dr(dut, shifted_in)
    dut.log.info(f"-> Shifted:")
    dut.log.info(f"\tin  = {hex(bin_list_to_num(shifted_in))}")
    dut.log.info(f"\tout = {hex(bin_list_to_num(shifted_out))}")

    if dr.read_only == False:
        shifted_out = await move_to_shift_dr(dut, shifted_in)
        dut.log.info(f"-> [RW] Comparing value shifted second time:")
        dut.log.info(f"\tin  = {hex(bin_list_to_num(shifted_in))}")
        dut.log.info(f"\tout = {hex(bin_list_to_num(shifted_out))}")
        assert(shifted_in == shifted_out),"Shifted out != Shifted in"



def test_dr():
    """
    Check all available data registers

    Test ID: 3
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


if cocotb.SIM_NAME:
    factory = TestFactory(run_test)
    factory.add_option(
        "jtag_dr",
        [
            (InstJTAG.BYPASS, 1, True),
            (InstJTAG.IC_RESET, 4, False),
            (InstJTAG.IDCODE, 32, True),
            (InstJTAG.ADDR_AXI_REG, 32, False),
            (InstJTAG.DATA_W_AXI_REG, 32, False),
            (InstJTAG.CTRL_AXI_REG, 39, False),
            (InstJTAG.STATUS_AXI_REG, 3, True),
        ],
    )
    factory.generate_tests()
