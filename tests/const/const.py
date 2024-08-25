#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : const.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
# Date              : 12.07.2023
# Last Modified Date: 25.08.2024
import os
import glob
from enum import Enum


class cfg:
    RST_CYCLES = 3
    CLK_100MHz = (10, "ns")
    TIMEOUT_TEST = (CLK_100MHz[0] * 200, "ns")

    TOPLEVEL = str(os.getenv("DUT"))
    SIMULATOR = str(os.getenv("SIM"))

    TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
    INC_DIR = os.path.join(TESTS_DIR, "../../rtl/include")
    RTL_DIR = os.path.join(TESTS_DIR, "../../rtl")

    VERILOG_SOURCES = []  # The sequence below is important...
    VERILOG_SOURCES = VERILOG_SOURCES + glob.glob(f"{RTL_DIR}/*.v", recursive=True)
    VERILOG_SOURCES = VERILOG_SOURCES + glob.glob(f"{INC_DIR}/*.sv", recursive=True)
    VERILOG_SOURCES = VERILOG_SOURCES + glob.glob(f"{RTL_DIR}/*.sv", recursive=True)

    EXTRA_ENV = {}
    EXTRA_ENV["COCOTB_HDL_TIMEPRECISION"] = os.getenv("TIMEPREC")
    EXTRA_ENV["COCOTB_HDL_TIMEUNIT"] = os.getenv("TIMEUNIT")
    TIMESCALE = os.getenv("TIMEUNIT") + "/" + os.getenv("TIMEPREC")
    INC_DIR = [os.path.join(TESTS_DIR, "../../rtl/include")]

    if SIMULATOR == "verilator":
        EXTRA_ARGS = [
            "--trace-fst",
            "--coverage",
            "--coverage-line",
            "--coverage-toggle",
            "--trace-structs",
        ]
        PLUS_ARGS = ["--trace"]
    else:
        EXTRA_ARGS = []


# JTAG TAP Controller States
class JTAGState(Enum):
    TEST_LOGIC_RESET = 0
    RUN_TEST_IDLE = 1
    SELECT_DR_SCAN = 2
    CAPTURE_DR = 3
    SHIFT_DR = 4
    EXIT1_DR = 5
    PAUSE_DR = 6
    EXIT2_DR = 7
    UPDATE_DR = 8
    SELECT_IR_SCAN = 9
    CAPTURE_IR = 10
    SHIFT_IR = 11
    EXIT1_IR = 12
    PAUSE_IR = 13
    EXIT2_IR = 14
    UPDATE_IR = 15


# JTAG FSM Model
class JTAGFSM:
    def __init__(self):
        self.state = JTAGState.TEST_LOGIC_RESET

    @property
    def fsm(self):
        return self.state
    
    def reset(self):
        self.state = JTAGState.TEST_LOGIC_RESET

    def transition(self, tms):
        if self.state == JTAGState.TEST_LOGIC_RESET:
            if tms == 0:
                self.state = JTAGState.RUN_TEST_IDLE
        elif self.state == JTAGState.RUN_TEST_IDLE:
            if tms == 1:
                self.state = JTAGState.SELECT_DR_SCAN
        elif self.state == JTAGState.SELECT_DR_SCAN:
            if tms == 0:
                self.state = JTAGState.CAPTURE_DR
            else:
                self.state = JTAGState.SELECT_IR_SCAN
        elif self.state == JTAGState.CAPTURE_DR:
            if tms == 0:
                self.state = JTAGState.SHIFT_DR
            else:
                self.state = JTAGState.EXIT1_DR
        elif self.state == JTAGState.SHIFT_DR:
            if tms == 1:
                self.state = JTAGState.EXIT1_DR
        elif self.state == JTAGState.EXIT1_DR:
            if tms == 0:
                self.state = JTAGState.PAUSE_DR
            else:
                self.state = JTAGState.UPDATE_DR
        elif self.state == JTAGState.PAUSE_DR:
            if tms == 1:
                self.state = JTAGState.EXIT2_DR
        elif self.state == JTAGState.EXIT2_DR:
            if tms == 0:
                self.state = JTAGState.SHIFT_DR
            else:
                self.state = JTAGState.UPDATE_DR
        elif self.state == JTAGState.UPDATE_DR:
            if tms == 0:
                self.state = JTAGState.RUN_TEST_IDLE
            else:
                self.state = JTAGState.SELECT_DR_SCAN
        elif self.state == JTAGState.SELECT_IR_SCAN:
            if tms == 0:
                self.state = JTAGState.CAPTURE_IR
            else:
                self.state = JTAGState.TEST_LOGIC_RESET
        elif self.state == JTAGState.CAPTURE_IR:
            if tms == 0:
                self.state = JTAGState.SHIFT_IR
            else:
                self.state = JTAGState.EXIT1_IR
        elif self.state == JTAGState.SHIFT_IR:
            if tms == 1:
                self.state = JTAGState.EXIT1_IR
        elif self.state == JTAGState.EXIT1_IR:
            if tms == 0:
                self.state = JTAGState.PAUSE_IR
            else:
                self.state = JTAGState.UPDATE_IR
        elif self.state == JTAGState.PAUSE_IR:
            if tms == 1:
                self.state = JTAGState.EXIT2_IR
        elif self.state == JTAGState.EXIT2_IR:
            if tms == 0:
                self.state = JTAGState.SHIFT_IR
            else:
                self.state = JTAGState.UPDATE_IR
        elif self.state == JTAGState.UPDATE_IR:
            if tms == 0:
                self.state = JTAGState.RUN_TEST_IDLE
            else:
                self.state = JTAGState.SELECT_DR_SCAN
        else:
            self.state = JTAGState.TEST_LOGIC_RESET
