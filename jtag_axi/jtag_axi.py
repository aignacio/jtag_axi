#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : jtag_axi.py
# License           : MIT license <Check LICENSE>
# Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
# Date              : 15.09.2024
# Last Modified Date: 15.09.2024
from abc import abstractmethod


class BaseJtagToAXI:
    @abstractmethod
    def __init__(self, 
                 addr_width: int = 32,
                 data_width: int = 32):
        """Initialize the interface (for hardware or DUT)."""
        self.addr_width = addr_width
        self.data_width = data_width
        

        pass

    @abstractmethod
    def write(self, data):
        """Send data through JTAG."""
        pass

    @abstractmethod
    def read(self):
        """Read data from JTAG."""
        pass

    @abstractmethod
    def reset(self):
        """Reset the JTAG interface."""
        pass
