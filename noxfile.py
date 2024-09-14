#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : noxfile.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
# Date              : 08.10.2023
# Last Modified Date: 14.09.2024

import nox
import os

TOP_MODULE = "jtag_axi_wrapper"
SRC_DIR = "rtl"
BUS_ARCH_DIR = "rtl/bus_arch_sv_pkg"
INCLUDE_DIR = "rtl/include"
SLANG_CMD = "slang"


@nox.session(python=["3.6", "3.7", "3.8", "3.9", "3.10", "3.12"], reuse_venv=True)
def run(session):
    session.env["DUT"] = TOP_MODULE
    session.env["SIM"] = "verilator"
    session.env["TIMEPREC"] = "1ps"
    session.env["TIMEUNIT"] = "1ns"
    session.install(
        "pytest",
        "pytest-sugar", 
        "pytest-xdist",
        "pytest-split",
        "cocotb >= 1.9.0",
        "cocotbext-axi"
    )
    session.run("py.test", "-n", "auto", "-rP", "tests", *session.posargs)


@nox.session(reuse_venv=True)
def sv_lint(session):
    slang_command = get_sv()
    slang_command.append("--lint-only")
    # session.log(f"Running: {' '.join(slang_command)}")
    session.run(*slang_command, external=True)


@nox.session(reuse_venv=True)
def sv_pre(session):
    slang_command = get_sv()
    slang_command.append("--preprocess")
    slang_command.append("--comments")
    slang_command += [">", "RM_ME_rtl_pp.sv"]
    # session.log(f"Running: {' '.join(slang_command)}")
    session.run("bash", "-c", " ".join(slang_command), external=True)


@nox.session(reuse_venv=True)
def sv_run(session):
    slang_command = get_sv()
    # session.log(f"Running: {' '.join(slang_command)}")
    session.run(*slang_command, external=True)


def get_sv():
    """Gather all SystemVerilog files and run slang with an include directory."""
    # Recursively find all .sv files in the SRC_DIR
    sv_files = []
    for root, _, files in os.walk(BUS_ARCH_DIR):
        for file in files:
            if file.endswith(".sv"):
                sv_files.append(os.path.join(root, file))
    for root, _, files in os.walk(INCLUDE_DIR):
        for file in files:
            if file.endswith(".sv"):
                sv_files.append(os.path.join(root, file))
    for root, _, files in os.walk(SRC_DIR):
        for file in files:
            if file.endswith(".sv"):
                sv_files.append(os.path.join(root, file))
    # Check if there are any SystemVerilog files found
    if not sv_files:
        session.error("No SystemVerilog files found in the source directory.")

    # Construct the slang command with include directory
    slang_command = [
        SLANG_CMD,
        "--include-directory",
        INCLUDE_DIR,
        "--top",
        TOP_MODULE,
        "-Weverything",
    # ] + sv_files
    ] + sv_files + ["--single-unit", "--libraries-inherit-macros"]

    return slang_command
