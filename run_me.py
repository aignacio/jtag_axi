from jtag_axi import JtagToAXIFTDI

handle = JtagToAXIFTDI()
handle.read_jdrs()
print(handle.read_axi(0x010))
print(handle.write_axi(0x010, 0xDEADBEEF))
