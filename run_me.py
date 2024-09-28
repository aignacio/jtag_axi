from jtag_axi import JtagToAXIFTDI

handle = JtagToAXIFTDI(debug=True)
handle.read_jdrs()
print(handle.write_axi(0x010, 0xDEADBEEF))
print(handle.read_axi(0x010))
