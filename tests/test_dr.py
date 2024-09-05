#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_dr.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 06.09.2024
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


@cocotb.test()
async def run_test(dut):
    await reset_fsm(dut)

    dut.log.info(f"------{InstJTAG.IC_RESET}------")
    await select_instruction(dut, InstJTAG.IC_RESET)
    ic_reset_random_val = gen_bin_list(4)
    val = await move_to_shift_dr(dut, ic_reset_random_val)
    dut.log.info(f"Shifted in/out: {ic_reset_random_val}/{val}")
    assert (
        bin_list_to_num(ic_reset_random_val) == dut.u_data_registers.ic_rst_ff.value
    ), "IC Reset does not match shifted data"

    dut.log.info(f"------{InstJTAG.BYPASS}------")
    await select_instruction(dut, InstJTAG.BYPASS)
    bypass_val = gen_bin_list(20)
    val = await move_to_shift_dr(dut, bypass_val)
    dut.log.info(f"Shifted in/out: \nIN = {bypass_val}\nOUT = {val} (SHIFTED BY ONE)")

    dut.log.info(f"------{InstJTAG.IDCODE}------")
    await select_instruction(dut, InstJTAG.IDCODE)
    idcode_val = gen_bin_list(32)
    val = await move_to_shift_dr(dut, idcode_val)
    dut.log.info(f"Shifted in/out: {hex(bin_list_to_num(idcode_val))}/{hex(bin_list_to_num(val))}")
    assert (
        bin_list_to_num(val) == 0x10f
    ), f"IDCODE does not match expected value shifted out ({bin_list_to_num(val)}) != 0x10F"

    dut.log.info(f"------{InstJTAG.ADDR_AXI_REGISTER}------")
    await select_instruction(dut, InstJTAG.ADDR_AXI_REGISTER)
    val_in = gen_bin_list(32)
    val_out = await move_to_shift_dr(dut, val_in)
    dut.log.info(f"Shifted in/out: {hex(bin_list_to_num(val_in))}/{hex(bin_list_to_num(val_out))}")
    # assert (
        # bin_list_to_num(val) == dut.u_data_registers.axi_ff.addr.value
    # ), "ADDR AXI Register does not match shifted data"

    dut.log.info(f"------{InstJTAG.DATA_AXI_REGISTER}------")
    await select_instruction(dut, InstJTAG.DATA_AXI_REGISTER)
    val_in = gen_bin_list(64)
    val_out = await move_to_shift_dr(dut, val_in)
    dut.log.info(f"Shifted in/out: {hex(bin_list_to_num(val_in))}/{hex(bin_list_to_num(val_out))}")
    # assert (
        # bin_list_to_num(val) == dut.u_data_registers.axi_ff.data.value
    # ), "DATA AXI Register does not match shifted data"

    dut.log.info(f"------{InstJTAG.MGMT_AXI_REGISTER}------")
    await select_instruction(dut, InstJTAG.MGMT_AXI_REGISTER)
    val_in = gen_bin_list(5)
    val_out = await move_to_shift_dr(dut, val_in)
    dut.log.info(f"Shifted in/out: {hex(bin_list_to_num(val_in))}/{hex(bin_list_to_num(val_out))}")
    # assert (
        # bin_list_to_num(val) == dut.u_data_registers.axi_ff.mgmt.flat.value
    # ), "MGMT AXI Register does not match shifted data"


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


if __name__ == "__main__":
    test_basic()
