/**
 * File              : jtag_axi_wrapper.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 09.09.2024
 * Last Modified Date: 30.09.2024
 */
module jtag_axi_wrapper
  import jtag_axi_pkg::*;
  import amba_axi_pkg::*;
#(
  parameter [31:0]  IDCODE_VAL     = 'hBADC0FFE,
  parameter int     IC_RST_WIDTH   = 4,
  parameter int     AXI_MASTER_ID  = 1,
  parameter int     AXI_TIMEOUT_CC = 4096
)(
  input                               trstn,
  input                               tck,
  input                               tms,
  input                               tdi,
  output  logic                       tdo,
  // Additional IOs
  output  logic [(IC_RST_WIDTH-1):0]  ic_rst,
  input   logic [31:0]                usercode_i,
  output  logic                       usercode_update_o,
  // AXI
  input                               clk_axi,
  input                               ares_axi,
  output  s_axi_mosi_t                jtag_axi_mosi_o,
  input   s_axi_miso_t                jtag_axi_miso_i
);
  s_axi_jtag_status_t         jtag_status;
  logic                       axi_status_rd;
  axi_afifo_t                 afifo_slots;
  s_axi_jtag_info_t           axi_info;
  logic                       axi_req_new;

  jtag_axi_tap_wrapper #(
    .IDCODE_VAL       (IDCODE_VAL),
    .IC_RST_WIDTH     (IC_RST_WIDTH)
  ) u_jtag_tap_wrapper (
    .trstn            (trstn),
    .tck              (tck),
    .tms              (tms),
    .tdi              (tdi),
    .tdo              (tdo),
    .ic_rst           (ic_rst),
    .usercode_i       (usercode_i),
    .usercode_update_o(usercode_update_o),
    // To/From AXI I/F
    .jtag_status_i    (jtag_status),
    .axi_status_rd_o  (axi_status_rd),
    .afifo_slots_i    (afifo_slots),
    .axi_info_o       (axi_info),
    .axi_req_new_o    (axi_req_new)
  );

  jtag_axi_dispatch #(
    .AXI_MASTER_ID    (AXI_MASTER_ID),
    .AXI_TIMEOUT_CC   (AXI_TIMEOUT_CC)
  ) u_axi_dispatch (
    .clk              (clk_axi),
    .ares             (ares_axi),
    .tck              (tck),
    .trstn            (trstn),
    .jtag_status_o    (jtag_status),
    .axi_status_rd_i  (axi_status_rd),
    .afifo_slots_o    (afifo_slots),
    .axi_info_i       (axi_info),
    .axi_req_new_i    (axi_req_new),
    .jtag_axi_mosi_o  (jtag_axi_mosi_o),
    .jtag_axi_miso_i  (jtag_axi_miso_i)
  );
endmodule
