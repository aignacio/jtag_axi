#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_axi.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 28.09.2024
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
async def run_test(dut, idle_generator=None, backpressure_generator=None):
    N = 20
    mem_size_kib = 10
    data_width = 32
    cocotb.start_soon(Clock(dut.clk_axi, *cfg.CLK_100MHz).start())
    # axi_ram = AxiRam(AxiBus.from_entity(dut), dut.clk_axi, dut.ares_axi,
                     # size=mem_size_kib*1024)

    address_space = AddressSpace(mem_size_kib*1024)
    ram = SparseMemoryRegion(mem_size_kib*1024)
    address_space.register_region(ram, 0x0000_0000)
    ram_pool = address_space.create_window_pool(0x0000_0000, mem_size_kib*1024)
    axi_ram = AxiSlave(AxiBus.from_entity(dut), dut.clk_axi, dut.ares_axi, target=address_space)

    if idle_generator:
        axi_ram.write_if.b_channel.set_pause_generator(idle_generator())
        axi_ram.read_if.r_channel.set_pause_generator(idle_generator())

    if backpressure_generator:
        axi_ram.write_if.aw_channel.set_pause_generator(backpressure_generator())
        axi_ram.write_if.w_channel.set_pause_generator(backpressure_generator())
        axi_ram.read_if.ar_channel.set_pause_generator(backpressure_generator())

    jtag = SimJtagToAXI(dut, freq=10e6, addr_width=32, data_width=data_width)

    dut.ares_axi.value = 1
    await ClockCycles(dut.clk_axi, 10)
    dut.ares_axi.value = 0

    await jtag.reset()
    await jtag.read_jdrs()

    # Start test setup
    address = random.sample(range(0, 2 * mem_size_kib * 1024, 8), N)
    value = [rnd_val(data_width) for _ in range(N)]
    if data_width == 32:
        size = [pick_random_value([1, 2, 4]) for _ in range(N)]
    else:
        size = [pick_random_value([1, 2, 4, 8]) for _ in range(N)]
    wstrb = [((1 << v) - 1) for v in size]

    expected = []
    for addr, val, sz in zip(address, value, size):
        resp, data = 0, 0
        if addr >= mem_size_kib * 1024:
            resp = JTAGToAXIStatus.JTAG_AXI_SLVERR.value
        else:
            resp = JTAGToAXIStatus.JTAG_AXI_OKAY.value
            if sz == 1:
                data = val & 0xFF
            elif sz == 2:
                data = val & 0xFFFF
            elif sz == 4:
                data = val & 0xFFFFFFFF
            elif sz == 8:
                data = val & 0xFFFFFFFFFFFFFFFF
        expected.append(JDRStatusAXI(data_rd=data, status=resp))

    resp = []
    # Perform the writes and reads
    for addr, val, sz, strb in zip(address, value, size, wstrb):
        await jtag.write_axi(addr, val, sz, strb)
        resp.append(await jtag.read_axi(addr, sz))

    # Compare all txns
    for index, (real, expect) in enumerate(zip(resp, expected)):
        if real != expect:
            dut.log.error("------ERROR------")
            dut.log.error(f"Txn ID: {index}")
            dut.log.error("DUT")
            dut.log.error(real)
            dut.log.error("Expected")
            dut.log.error(expect)
            assert real == expect, "DUT != Expected"


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


if cocotb.SIM_NAME:
    factory = TestFactory(run_test)
    factory.add_option("idle_generator", [None, cycle_pause])
    factory.add_option("backpressure_generator", [None, cycle_pause])
    factory.generate_tests()
