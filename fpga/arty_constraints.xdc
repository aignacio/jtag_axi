## Clock signal

set_property -dict { PACKAGE_PIN H5    IOSTANDARD LVCMOS33 } [get_ports { ic_rst[3] }]; #IO_L24N_T3_35 Sch=led[4]
#set_property -dict { PACKAGE_PIN J5    IOSTANDARD LVCMOS33 } [get_ports { addr[31] }]; #IO_25_35 Sch=led[5]
set_property -dict { PACKAGE_PIN T9    IOSTANDARD LVCMOS33 } [get_ports { ic_rst[0] }]; #IO_L24P_T3_A01_D17_14 Sch=led[6]
#set_property -dict { PACKAGE_PIN T10   IOSTANDARD LVCMOS33 } [get_ports { data[31] }]; #IO_L24N_T3_A00_D16_14 Sch=led[7]

## Pmod Header JA
set_property -dict { PACKAGE_PIN G13 IOSTANDARD LVCMOS33 PULLUP TRUE } [get_ports { trstn }]; #IO_0_15 Sch=ja[1] NOT CONNECTED
set_property -dict { PACKAGE_PIN D13 IOSTANDARD LVCMOS33 } [get_ports { tms }]; #Sch=ja[7]
set_property -dict { PACKAGE_PIN B18 IOSTANDARD LVCMOS33 } [get_ports { tck }]; #Sch=ja[8]
set_property -dict { PACKAGE_PIN A18 IOSTANDARD LVCMOS33 } [get_ports { tdo }]; #Sch=ja[9]
set_property -dict { PACKAGE_PIN K16 IOSTANDARD LVCMOS33 } [get_ports { tdi }]; #Sch=ja[10]
set_property -dict { PACKAGE_PIN E3  IOSTANDARD LVCMOS33 } [get_ports { clk_axi }];
set_property -dict { PACKAGE_PIN A8  IOSTANDARD LVCMOS33 } [get_ports { ares_axi }]; #IO_L12N_T1_MRCC_16 Sch=sw[0]

create_clock -add -name jtag_clk_pin -period 100.00 -waveform {0 50} [get_ports { tck }];
set_property CLOCK_DEDICATED_ROUTE FALSE [get_nets tck]

create_clock -add -name axi_clk_pin -period 10.00 -waveform {0 5} [get_ports { clk_axi }];

# Downgrade Errors to Warnings on unconstrainted IOs - Don't care for now
set_property SEVERITY {Warning} [get_drc_checks NSTD-1]
set_property SEVERITY {Warning} [get_drc_checks UCIO-1]
