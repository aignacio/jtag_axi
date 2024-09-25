#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : test_timeout.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 26.09.2024
import cocotb
import logging
import pytest
import random
import os
import sys
import itertools

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path
from random import randrange
from const.const import cfg
from const.help_fn import reset_fsm, select_instruction, move_to_shift_dr
from jtag_axi.jtag_base import InstJTAG, JTAGToAXIStatus, JDRStatusAXI
from jtag_axi.jtag_axi import SimJtagToAXI
from cocotb.triggers import ClockCycles, RisingEdge
from cocotb.clock import Clock
from cocotb.regression import TestFactory
from cocotb.result import TestFailure
from cocotb.runner import get_runner
from enum import Enum
from cocotbext.axi import AddressSpace, SparseMemoryRegion
from cocotbext.axi import AxiBus, AxiLiteMaster, AxiSlave
from cocotb.result import TestFailure, TestSuccess

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
async def run_test(dut, idle_generator=None, backpressure_generator=None, timeout=None):
    N = 1
    mem_size_kib = 10
    data_width = 32

    dut.to_awready.value = 0
    dut.to_arready.value = 0
    dut.to_wready.value = 0
    dut.to_rvalid.value = 0
    dut.to_bvalid.value = 0
    exp = 0

    cocotb.start_soon(Clock(dut.clk_axi, *cfg.CLK_100MHz).start())

    address_space = AddressSpace(mem_size_kib * 1024)
    ram = SparseMemoryRegion(mem_size_kib * 1024)
    address_space.register_region(ram, 0x0000_0000)
    ram_pool = address_space.create_window_pool(0x0000_0000, mem_size_kib * 1024)
    axi_ram = AxiSlave(
        AxiBus.from_entity(dut), dut.clk_axi, dut.ares_axi, target=address_space
    )

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

    if timeout == None:
        timeout_dut = random.choice(
            [
                dut.to_awready,
                dut.to_arready,
                dut.to_wready,
                dut.to_rvalid,
                dut.to_bvalid,
            ]
        )
    elif timeout == "awready":
        timeout_dut = dut.to_awready
        exp = JTAGToAXIStatus.JTAG_TIMEOUT_AW
    elif timeout == "arready":
        timeout_dut = dut.to_arready
        exp = JTAGToAXIStatus.JTAG_TIMEOUT_AR
    elif timeout == "wready":
        timeout_dut = dut.to_wready
        exp = JTAGToAXIStatus.JTAG_TIMEOUT_W
    elif timeout == "rvalid":
        timeout_dut = dut.to_rvalid
        exp = JTAGToAXIStatus.JTAG_TIMEOUT_R
    elif timeout == "bvalid":
        timeout_dut = dut.to_bvalid
        exp = JTAGToAXIStatus.JTAG_TIMEOUT_B

    dut.log.info(f"{timeout_dut._name} was randomly selected and forced to 0.")
    # Verilator does not support force =/
    # timeout_dut.value = cocotb.handle.Force(0x0)
    # timeout_dut.value = cocotb.handle.Freeze()
    timeout_dut.value = 1

    # Start test setup
    address = random.sample(range(0, 2 * mem_size_kib * 1024, 8), N)
    value = [rnd_val(data_width) for _ in range(N)]
    if data_width == 32:
        size = [pick_random_value([1, 2, 4]) for _ in range(N)]
    else:
        size = [pick_random_value([1, 2, 4, 8]) for _ in range(N)]
    wstrb = [((1 << v) - 1) for v in size]

    resp = []
    # Perform the writes and reads
    for addr, val, sz, strb in zip(address, value, size, wstrb):
        resp.append(await jtag.write_axi(addr, val, sz, strb))
        resp.append(await jtag.read_axi(addr, sz))

    for ret in resp:
        if ret.status in [
            JTAGToAXIStatus.JTAG_TIMEOUT_AR,
            JTAGToAXIStatus.JTAG_TIMEOUT_R,
            JTAGToAXIStatus.JTAG_TIMEOUT_AW,
            JTAGToAXIStatus.JTAG_TIMEOUT_W,
            JTAGToAXIStatus.JTAG_TIMEOUT_B,
        ]:
            if (ret.status == exp) or (timeout == None):
                raise TestSuccess("Timeout detected!")
    raise TestFailure("Expected timeout to be triggered!")


def test_timeout():
    """
    Test to expecting timeouts

    Test ID: 5
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
        # clean=True,
        timescale=cfg.TIMESCALE,
        waves=True,
        build_dir=SIM_BUILD,
    )

    runner.test(
        hdl_toplevel="jtag_axi_wrapper_tb",
        test_module=test_name,
        plusargs=cfg.PLUS_ARGS,
    )


if cocotb.SIM_NAME:
    factory = TestFactory(run_test)
    factory.add_option("idle_generator", [None, cycle_pause])
    factory.add_option("backpressure_generator", [None, cycle_pause])
    factory.add_option("timeout", ["awready", "arready", "wready", "rvalid", "bvalid"])
    factory.generate_tests()
