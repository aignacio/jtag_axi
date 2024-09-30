#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_userdata.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 30.09.2024
import cocotb
import logging
import pytest
import random
import os
import sys
import itertools

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
from random import randrange
from const.const import cfg
from const.help_fn import reset_fsm, select_instruction, move_to_shift_dr
from jtag_axi.jtag_base import JTAGToAXIStatus, JDRStatusAXI, InstJTAG
from jtag_axi.jtag_axi_sim import SimJtagToAXI
from cocotb.triggers import ClockCycles, RisingEdge
from cocotb.clock import Clock
from cocotb.regression import TestFactory
from cocotb.result import TestFailure
from cocotb.runner import get_runner
from enum import Enum
from cocotbext.axi import AddressSpace, SparseMemoryRegion
from cocotbext.axi import AxiBus, AxiLiteMaster, AxiSlave
from cocotb.utils import get_sim_time

CLK_100MHz = (10, "ns")
TestFailure.__test__ = False


def rnd_val(bit: int = 0, zero: bool = True):
    if zero is True:
        return random.randint(0, (2**bit) - 1)
    else:
        return random.randint(1, (2**bit) - 1)


def pick_random_value(input_list):
    if input_list:
        return random.choice(input_list)
    else:
        return None  # Return None if the list is empty


def bin_list_to_num(binary_list):
    # Join the list into a string and convert to an integer using base 2
    binary_string = "".join(map(str, binary_list))
    return int(binary_string, 2)


def convert_to_bin_list(value, bits):
    # Convert the number to its binary representation and remove the '0b' prefix
    bin_str = bin(value & ((1 << bits) - 1))[2:].zfill(bits)
    # Convert the string representation of the binary number to a list of integers
    return [int(bit) for bit in bin_str]


def cycle_pause():
    return itertools.cycle([1, 1, 1, 0])


@cocotb.test()
async def run_test(dut):
    N = 500

    jtag = SimJtagToAXI(dut, freq=10e6, addr_width=32, data_width=32)
    cocotb.start_soon(Clock(dut.clk_axi, *cfg.CLK_100MHz).start())

    dut.ares_axi.value = 1
    await ClockCycles(dut.clk_axi, 10)
    dut.ares_axi.value = 0

    await jtag.reset()
    await jtag.read_jdrs()

    userdata_width = InstJTAG.USERDATA.value[1]

    await jtag.write_userdata(rnd_val(userdata_width)) 

    start_sim_time = get_sim_time(units='ns')
    for _ in range(N):
        await jtag.write_fwd_userdata(rnd_val(userdata_width)) 

    end_sim_time = get_sim_time(units='ns')
    delta = end_sim_time-start_sim_time
    bw = (((userdata_width/8)*N)/1024/1024)/(delta*(10**-9))
    dut.log.info(f"Sim time in ns: {delta:.2} ns")
    dut.log.info(f"Throughput: {bw:.2} MiB/s")


def test_userdata():
    """
    Test USERDATA

    Test ID: 6
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
    # factory.generate_tests()
