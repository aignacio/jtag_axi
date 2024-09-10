#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_dr.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 10.09.2024
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


class AccessMode(Enum):
    RO = 1
    RW = 2


class JTAGDataRegister:
    def __init__(self, dut, ir_ins, shift_length, ac, mask):
        self.dut = dut
        self.ir_ins = ir_ins
        self.shift_length = shift_length
        self.access = ac
        self.mask = mask

    def display(self):
        self.dut.log.info("------------------------------")
        self.dut.log.info(f"IR Instruction: {self.ir_ins}")
        self.dut.log.info(f"Shift Length: {self.shift_length}")
        self.dut.log.info(f"Access: {self.access}")
        self.dut.log.info(f"Mask: {self.mask}")


@cocotb.test()
async def run_test(dut, jtag_dr=(InstJTAG.BYPASS, 1, AccessMode.RO, 0x1)):
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

    if dr.access == AccessMode.RW:
        shifted_out = await move_to_shift_dr(dut, shifted_in)
        dut.log.info(f"-> [RW] Comparing value shifted second time:")
        dut.log.info(f"\tin  = {hex(bin_list_to_num(shifted_in) & dr.mask)}")
        dut.log.info(f"\tout = {hex(bin_list_to_num(shifted_out))}")
        shifted_in = bin_list_to_num(shifted_in) & dr.mask
        shifted_out = bin_list_to_num(shifted_out)
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
            (InstJTAG.BYPASS, 1, AccessMode.RO, 0x1),
            (InstJTAG.IC_RESET, 4, AccessMode.RW, 0xf),
            (InstJTAG.IDCODE, 32, AccessMode.RO, 0xfff_ffff),
            (InstJTAG.ADDR_AXI_REG, 32, AccessMode.RW, 0xffff_ffff),
            (InstJTAG.DATA_W_AXI_REG, 32, AccessMode.RW, 0xffff_ffff),
            (InstJTAG.CTRL_AXI_REG, 8, AccessMode.RW, 0xc7),
            (InstJTAG.STATUS_AXI_REG, 37, AccessMode.RO, 0x1fffffffff),
        ],
    )
    factory.generate_tests()
