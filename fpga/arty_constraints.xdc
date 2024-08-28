## Clock signal

set_property -dict { PACKAGE_PIN H5    IOSTANDARD LVCMOS33 } [get_ports { addr[0] }]; #IO_L24N_T3_35 Sch=led[4]
set_property -dict { PACKAGE_PIN J5    IOSTANDARD LVCMOS33 } [get_ports { addr[31] }]; #IO_25_35 Sch=led[5]
set_property -dict { PACKAGE_PIN T9    IOSTANDARD LVCMOS33 } [get_ports { data[0] }]; #IO_L24P_T3_A01_D17_14 Sch=led[6]
set_property -dict { PACKAGE_PIN T10   IOSTANDARD LVCMOS33 } [get_ports { data[31] }]; #IO_L24N_T3_A00_D16_14 Sch=led[7]

## Pmod Header JB
set_property -dict { PACKAGE_PIN E15   IOSTANDARD LVCMOS33 PULLUP TRUE } [get_ports { trstn }]; #IO_L11P_T1_SRCC_15 Sch=jb_p[1] - jb[0]
set_property -dict { PACKAGE_PIN E16   IOSTANDARD LVCMOS33 } [get_ports { tck }]; #IO_L11N_T1_SRCC_15 Sch=jb_n[1]   - jb[1]
set_property -dict { PACKAGE_PIN D15   IOSTANDARD LVCMOS33 } [get_ports { tms }]; #IO_L12P_T1_MRCC_15 Sch=jb_p[2]   - jb[2]
set_property -dict { PACKAGE_PIN C15   IOSTANDARD LVCMOS33 } [get_ports { tdi }]; #IO_L12N_T1_MRCC_15 Sch=jb_n[2]   - jb[3]
set_property -dict { PACKAGE_PIN J17   IOSTANDARD LVCMOS33 } [get_ports { tdo }]; #IO_L23P_T3_FOE_B_15 Sch=jb_p[3]  - jb[4]

create_clock -add -name sys_clk_pin -period 1000.00 -waveform {0 500} [get_ports {tck}];
