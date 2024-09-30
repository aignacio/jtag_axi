module jtag_axi_wrapper_tb
  import jtag_axi_pkg::*;
  import amba_axi_pkg::*;
#(
  parameter [31:0]  IDCODE_VAL     = 'hBADC0FFE,
  parameter int     IC_RST_WIDTH   = 4,
  parameter int     USERDATA_WIDTH = 4,
  parameter int     AXI_MASTER_ID  = 1,
  parameter int     AXI_TIMEOUT_CC = 4096
)(
  input                                       trstn,
  input                                       tck,
  input                                       tms,
  input                                       tdi,
  output  logic                               tdo,
  output  logic [(IC_RST_WIDTH-1):0]          ic_rst,
  // AXI
  input                                       clk_axi,
  input                                       ares_axi,

  // Write Address Channel
  output  logic [`AXI_TXN_ID_WIDTH-1:0]       awid,
  output  logic [`AXI_ADDR_WIDTH-1:0]         awaddr,
  output  logic [`AXI_ALEN_WIDTH-1:0]         awlen,
  output  logic [`AXI_ASIZE_WIDTH-1:0]        awsize,
  output  logic [1:0]                         awburst,
  output  logic                               awlock,
  output  logic [3:0]                         awcache,
  output  logic [2:0]                         awprot,
  output  logic [3:0]                         awqos,
  output  logic [3:0]                         awregion,
  output  logic [`AXI_USER_REQ_WIDTH-1:0]     awuser,
  output  logic                               awvalid,
  input   logic                               awready,

  // Write Data Channel
  output  logic [`AXI_DATA_WIDTH-1:0]         wdata,
  output  logic [(`AXI_DATA_WIDTH/8)-1:0]     wstrb,
  output  logic                               wlast,
  output  logic [`AXI_USER_DATA_WIDTH-1:0]    wuser,
  output  logic                               wvalid,
  input   logic                               wready,

  // Write Response Channel
  input   logic [`AXI_TXN_ID_WIDTH-1:0]       bid,
  input   logic [1:0]                         bresp,
  input   logic [`AXI_USER_RESP_WIDTH-1:0]    buser,
  input   logic                               bvalid,
  output  logic                               bready,

  // Read Address Channel
  output  logic [`AXI_TXN_ID_WIDTH-1:0]       arid,
  output  logic [`AXI_ADDR_WIDTH-1:0]         araddr,
  output  logic [`AXI_ALEN_WIDTH-1:0]         arlen,
  output  logic [`AXI_ASIZE_WIDTH-1:0]        arsize,
  output  logic [1:0]                         arburst,
  output  logic                               arlock,
  output  logic [3:0]                         arcache,
  output  logic [2:0]                         arprot,
  output  logic [3:0]                         arqos,
  output  logic [3:0]                         arregion,
  output  logic [`AXI_USER_REQ_WIDTH-1:0]     aruser,
  output  logic                               arvalid,
  input   logic                               arready,

  // Read Data Channel
  input   logic [`AXI_TXN_ID_WIDTH-1:0]       rid,
  input   logic [`AXI_DATA_WIDTH-1:0]         rdata,
  input   logic [1:0]                         rresp,
  input   logic                               rlast,
  input   logic [`AXI_USER_REQ_WIDTH-1:0]     ruser,
  input   logic                               rvalid,
  output  logic                               rready,

  //Timeout
  input   logic                               to_awready,
  input   logic                               to_arready,
  input   logic                               to_wready,
  input   logic                               to_bvalid,
  input   logic                               to_rvalid
);

  // Declare the AXI interfaces as packed structs
  s_axi_mosi_t jtag_axi_mosi_o;
  s_axi_miso_t jtag_axi_miso_i;

  // Assign individual signals to the packed struct fields
  assign awid                    = jtag_axi_mosi_o.awid;
  assign awaddr                  = jtag_axi_mosi_o.awaddr;
  assign awlen                   = jtag_axi_mosi_o.awlen;
  assign awsize                  = jtag_axi_mosi_o.awsize;
  assign awburst                 = jtag_axi_mosi_o.awburst;
  assign awlock                  = jtag_axi_mosi_o.awlock;
  assign awcache                 = jtag_axi_mosi_o.awcache;
  assign awprot                  = jtag_axi_mosi_o.awprot;
  assign awqos                   = jtag_axi_mosi_o.awqos;
  assign awregion                = jtag_axi_mosi_o.awregion;
  assign awuser                  = jtag_axi_mosi_o.awuser;
  assign awvalid                 = jtag_axi_mosi_o.awvalid;
  assign jtag_axi_miso_i.awready = to_awready ? 1'b0 : awready;

  assign wdata                   = jtag_axi_mosi_o.wdata;
  assign wstrb                   = jtag_axi_mosi_o.wstrb;
  assign wlast                   = jtag_axi_mosi_o.wlast;
  assign wuser                   = jtag_axi_mosi_o.wuser;
  assign wvalid                  = jtag_axi_mosi_o.wvalid;
  assign jtag_axi_miso_i.wready  = to_wready ? 1'b0 : wready;

  assign jtag_axi_miso_i.bid     = bid;
  assign jtag_axi_miso_i.bresp   = axi_resp_t'(bresp);
  assign jtag_axi_miso_i.buser   = buser;
  assign jtag_axi_miso_i.bvalid  = to_bvalid | to_wready ? 1'b0 : bvalid;
  assign bready                  = jtag_axi_mosi_o.bready;

  assign arid                    = jtag_axi_mosi_o.arid;
  assign araddr                  = jtag_axi_mosi_o.araddr;
  assign arlen                   = jtag_axi_mosi_o.arlen;
  assign arsize                  = jtag_axi_mosi_o.arsize;
  assign arburst                 = jtag_axi_mosi_o.arburst;
  assign arlock                  = jtag_axi_mosi_o.arlock;
  assign arcache                 = jtag_axi_mosi_o.arcache;
  assign arprot                  = jtag_axi_mosi_o.arprot;
  assign arqos                   = jtag_axi_mosi_o.arqos;
  assign arregion                = jtag_axi_mosi_o.arregion;
  assign aruser                  = jtag_axi_mosi_o.aruser;
  assign arvalid                 = jtag_axi_mosi_o.arvalid;
  assign jtag_axi_miso_i.arready = to_arready ? 1'b0 : arready;

  assign jtag_axi_miso_i.rid     = rid;
  assign jtag_axi_miso_i.rdata   = rdata;
  assign jtag_axi_miso_i.rresp   = axi_resp_t'(rresp);
  assign jtag_axi_miso_i.rlast   = rlast;
  assign jtag_axi_miso_i.ruser   = ruser;
  assign jtag_axi_miso_i.rvalid  = to_rvalid ? 1'b0 : rvalid;
  assign rready                  = jtag_axi_mosi_o.rready;

  // Instantiate the original jtag_axi_if module, passing the separated AXI signals
  jtag_axi_wrapper #(
    .IDCODE_VAL               (IDCODE_VAL),
    .IC_RST_WIDTH             (IC_RST_WIDTH),
    .USERDATA_WIDTH           (USERDATA_WIDTH),
    .AXI_MASTER_ID            (AXI_MASTER_ID),
    .AXI_TIMEOUT_CC           (AXI_TIMEOUT_CC)
  ) u_jtag_axi_wrapper (
    .trstn                    (trstn),
    .tck                      (tck),
    .tms                      (tms),
    .tdi                      (tdi),
    .tdo                      (tdo),
    .ic_rst                   (ic_rst),
    .usercode_i               ('hBABE_BABE),
    .usercode_update_o        (),
    .userdata_o               (),
    .userdata_update_o        (),
    .clk_axi                  (clk_axi),
    .ares_axi                 (ares_axi),
    .jtag_axi_mosi_o          (jtag_axi_mosi_o),
    .jtag_axi_miso_i          (jtag_axi_miso_i)
  );

endmodule
