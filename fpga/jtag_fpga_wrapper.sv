module jtag_fpga_wrapper
  import jtag_axi_pkg::*;
  import amba_axi_pkg::*;
#(
  parameter [31:0]  IDCODE_VAL    = 'hBADC0FFE,
  parameter int     IC_RST_WIDTH  = 4,
  parameter int     AXI_MASTER_ID = 1
)(
  input                               trstn,
  input                               tck,
  input                               tms,
  input                               tdi,
  output  logic                       tdo,
  output  logic [(IC_RST_WIDTH-1):0]  ic_rst,
  input                               clk_axi,
  input                               ares_axi
);
  // Instantiate the original jtag_axi_if module, passing the separated AXI signals
  jtag_axi_wrapper #(
    .IDCODE_VAL               (IDCODE_VAL),
    .IC_RST_WIDTH             (IC_RST_WIDTH),
    .AXI_MASTER_ID            (AXI_MASTER_ID)
  ) u_jtag_axi_wrapper (
    .trstn                    (trstn),
    .tck                      (tck),
    .tms                      (tms),
    .tdi                      (tdi),
    .tdo                      (tdo),
    .ic_rst                   (ic_rst),
    .clk_axi                  (clk_axi),
    .ares_axi                 (ares_axi),
    .jtag_axi_mosi_o          (),
    .jtag_axi_miso_i          ('0)
  );


endmodule
