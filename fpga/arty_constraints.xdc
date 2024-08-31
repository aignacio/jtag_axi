## Clock signal

set_property -dict { PACKAGE_PIN H5    IOSTANDARD LVCMOS33 } [get_ports { addr[0] }]; #IO_L24N_T3_35 Sch=led[4]
set_property -dict { PACKAGE_PIN J5    IOSTANDARD LVCMOS33 } [get_ports { addr[31] }]; #IO_25_35 Sch=led[5]
set_property -dict { PACKAGE_PIN T9    IOSTANDARD LVCMOS33 } [get_ports { data[0] }]; #IO_L24P_T3_A01_D17_14 Sch=led[6]
set_property -dict { PACKAGE_PIN T10   IOSTANDARD LVCMOS33 } [get_ports { data[31] }]; #IO_L24N_T3_A00_D16_14 Sch=led[7]

## Pmod Header JA
set_property -dict { PACKAGE_PIN G13 IOSTANDARD LVCMOS33 PULLUP TRUE } [get_ports { trstn }]; #IO_0_15 Sch=ja[1] NOT CONNECTED
set_property -dict { PACKAGE_PIN D13 IOSTANDARD LVCMOS33 } [get_ports { tms }]; #Sch=ja[7]
set_property -dict { PACKAGE_PIN B18 IOSTANDARD LVCMOS33 } [get_ports { tck }]; #Sch=ja[8]
set_property -dict { PACKAGE_PIN A18 IOSTANDARD LVCMOS33 } [get_ports { tdo }]; #Sch=ja[9]
set_property -dict { PACKAGE_PIN K16 IOSTANDARD LVCMOS33 } [get_ports { tdi }]; #Sch=ja[10]

create_clock -add -name sys_clk_pin -period 1000.00 -waveform {0 500} [get_ports { tck }];
set_property CLOCK_DEDICATED_ROUTE FALSE [get_nets tck]

# Downgrade Errors to Warnings on unconstrainted IOs - Don't care for now:w
set_property SEVERITY {Warning} [get_drc_checks NSTD-1]
set_property SEVERITY {Warning} [get_drc_checks UCIO-1]
