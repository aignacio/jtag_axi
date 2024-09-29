from jtag_axi import JtagToAXIFTDI
import time

jtag = JtagToAXIFTDI(device='ftdi://ftdi:2232:3:4/1', debug=True, freq=10e6)
jtag.read_jdrs()
for i in range(1000000):
    jtag.write_ic_reset(i%2)
    time.sleep(0.001)

# print(jtag.write_axi(0x010, 0xDEADBEEF))
# print(jtag.read_axi(0x010))
