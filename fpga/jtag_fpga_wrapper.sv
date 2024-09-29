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
  s_axi_mosi_t [1:0] slaves_axi_mosi;
  s_axi_miso_t [1:0] slaves_axi_miso;

  s_axi_mosi_t       masters_axi_mosi;
  s_axi_miso_t       masters_axi_miso;

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
    .jtag_axi_mosi_o          (masters_axi_mosi),
    .jtag_axi_miso_i          (masters_axi_miso)
  );

  axi_interconnect_wrapper #(
    .N_MASTERS     (1),
    .N_SLAVES      (2),
    .AXI_TID_WIDTH (8),
    .M_BASE_ADDR   ({32'h1000_0000,
                     32'h0000_0000}),
    .M_ADDR_WIDTH  ({32'd17,
                     32'd17})
  ) u_axi_interconnect (
    .clk              (clk_axi),
    .arst             (~ares_axi),
    .*
  );

  axi_mem_wrapper #(
    .MEM_KB   (32),
    .ID_WIDTH (8)
  ) u_imem_1 (
    .clk      (clk_axi),
    .rst      (ares_axi),
    .axi_mosi (slaves_axi_mosi[0]),
    .axi_miso (slaves_axi_miso[0])
  );

  axi_mem_wrapper #(
    .MEM_KB   (32),
    .ID_WIDTH (8)
  ) u_imem_2 (
    .clk      (clk_axi),
    .rst      (ares_axi),
    .axi_mosi (slaves_axi_mosi[1]),
    .axi_miso (slaves_axi_miso[1])
  );

  //ila_0 u_ila_0 (
    //.clk    (clk_axi),
    //.probe0 (masters_axi_mosi.awaddr),
    //.probe1 (masters_axi_miso.awready),
    //.probe2 (masters_axi_mosi.awvalid),
    //.probe3 (masters_axi_mosi.araddr),
    //.probe4 (masters_axi_miso.arready),
    //.probe5 (masters_axi_mosi.arvalid),
    //.probe6 (masters_axi_mosi.wdata),
    //.probe7 (masters_axi_mosi.wvalid).
    //.probe8 (masters_axi_miso.wready)
    //.probe9 (slaves_axi_mosi[0].awaddr),
    //.probe10(slaves_axi_mosi[0].awvalid),
    //.probe11(slaves_axi_miso[0].awready),
    //.probe12(slaves_axi_mosi[1].awaddr),
    //.probe13(slaves_axi_mosi[1].awvalid),
    //.probe14(slaves_axi_miso[1].awready),
    //.probe15(ares_axi)
  //);
endmodule
