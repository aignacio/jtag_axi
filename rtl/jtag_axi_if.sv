/**
 * File              : jtag_axi_if.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 11.09.2024
 * Last Modified Date: 23.09.2024
 */
module jtag_axi_if
  import amba_axi_pkg::*;
  import jtag_axi_pkg::*;
#(
  parameter int AXI_MASTER_ID  = 0,
  parameter int AXI_TIMEOUT_CC = 4096
)(
  input                         tck,
  input                         trstn,
  input                         clk,
  input                         ares,
  output  logic                 timeout_aw_jtag_o,
  output  logic                 timeout_ar_jtag_o,
  output  logic                 timeout_w_jtag_o,
  output  logic                 timeout_b_jtag_o,
  output  logic                 timeout_r_jtag_o,
  // FIFO I/F - Incoming txn request
  input                         fifo_rd_txn_empty,
  input   s_axi_afifo_to_axi_t  fifo_rd_txn,
  output  logic                 fifo_rd_en,
  // FIFO I/F - Incoming txn request - wr data
  input                         fifo_wr_data_txn_empty,
  input   axi_data_t            fifo_wr_data,
  input   axi_wr_strb_t         fifo_wr_strb,
  output  logic                 fifo_wr_data_en,
  // FIFO I/F - Outgoing txn responses
  input                         fifo_wr_txn_full,
  output  s_axi_jtag_status_t   fifo_wr_resp,
  output  logic                 fifo_wr_en,
  // AXI I/F
  output  s_axi_mosi_t          jtag_axi_mosi_o,
  input   s_axi_miso_t          jtag_axi_miso_i
);
  typedef enum logic {
    AXI_READ_OP,
    AXI_WRITE_OP
  } int_op_type_t;

  logic fifo_wr_en_addr_op;
  logic fifo_rd_en_addr_op;
  logic fifo_empty_addr_op;
  logic fifo_full_addr_op;

  logic aw_timeout;
  logic ar_timeout;
  logic w_timeout;
  logic b_timeout;
  logic r_timeout;

  logic timeout_axi_aw;
  logic timeout_axi_aw_ff;
  logic timeout_axi_ar;
  logic timeout_axi_ar_ff;
  logic timeout_axi_w;
  logic timeout_axi_w_ff;
  logic timeout_axi_b;
  logic timeout_axi_b_ff;
  logic timeout_axi_r;
  logic timeout_axi_r_ff;

  int_op_type_t op_type_in, op_type_out;

  always_comb begin
    jtag_axi_mosi_o = s_axi_mosi_t'('0);
    fifo_rd_en = 1'b0;
    fifo_wr_resp = s_axi_jtag_status_t'('0);
    fifo_wr_en = 1'b0;
    fifo_wr_en_addr_op = 1'b0;
    fifo_rd_en_addr_op = 1'b0;
    op_type_in = AXI_READ_OP;
    fifo_wr_data_en = 1'b0;

    fifo_wr_resp.data_rd = jtag_axi_miso_i.rdata;
    jtag_axi_mosi_o.awid = axi_tid_t'(AXI_MASTER_ID);
    jtag_axi_mosi_o.arid = axi_tid_t'(AXI_MASTER_ID);

    jtag_axi_mosi_o.awaddr = fifo_rd_txn.addr;
    jtag_axi_mosi_o.awsize = fifo_rd_txn.size;
    jtag_axi_mosi_o.awburst = AXI_INCR;

    jtag_axi_mosi_o.araddr = fifo_rd_txn.addr;
    jtag_axi_mosi_o.arsize = fifo_rd_txn.size;
    jtag_axi_mosi_o.arburst = AXI_INCR;

    // Address channel
    if (~fifo_rd_txn_empty && ~fifo_full_addr_op) begin
      if (fifo_rd_txn.txn_type) begin : aw_axi
        jtag_axi_mosi_o.awvalid = 1'b1;
        fifo_rd_en = jtag_axi_miso_i.awready;
        fifo_wr_en_addr_op = jtag_axi_miso_i.awready;
        op_type_in = AXI_WRITE_OP;
      end : aw_axi
      else begin : ar_axi
        jtag_axi_mosi_o.arvalid = 1'b1;
        fifo_rd_en = jtag_axi_miso_i.arready;
        fifo_wr_en_addr_op = jtag_axi_miso_i.arready;
        op_type_in = AXI_READ_OP;
      end : ar_axi
    end

    if (~fifo_wr_data_txn_empty) begin : w_axi
      // Write data path
      jtag_axi_mosi_o.wvalid = 1'b1;
      jtag_axi_mosi_o.wdata = fifo_wr_data;
      jtag_axi_mosi_o.wstrb = fifo_wr_strb;
      jtag_axi_mosi_o.wlast = 1'b1;
      fifo_wr_data_en = jtag_axi_miso_i.wready;
    end : w_axi

    if (~fifo_empty_addr_op) begin
      if (op_type_out == AXI_READ_OP) begin : r_axi
        jtag_axi_mosi_o.rready = 1'b1;
        // We don't need to check the rlast as
        // it's always a single beat burst
        if (jtag_axi_miso_i.rvalid && ~fifo_wr_txn_full) begin
          fifo_rd_en_addr_op = 1'b1;
          fifo_wr_en = 1'b1;
          unique case (jtag_axi_miso_i.rresp)
            AXI_OKAY:   fifo_wr_resp.status = JTAG_AXI_OKAY;
            AXI_EXOKAY: fifo_wr_resp.status = JTAG_AXI_EXOKAY;
            AXI_SLVERR: fifo_wr_resp.status = JTAG_AXI_SLVERR;
            AXI_DECERR: fifo_wr_resp.status = JTAG_AXI_DECERR;
          endcase
        end
      end : r_axi
      else begin : b_axi
        jtag_axi_mosi_o.bready = 1'b1;
        if (jtag_axi_miso_i.bvalid && ~fifo_wr_txn_full) begin
          fifo_rd_en_addr_op = 1'b1;
          fifo_wr_en = 1'b1;
          unique case (jtag_axi_miso_i.bresp)
            AXI_OKAY:   fifo_wr_resp.status = JTAG_AXI_OKAY;
            AXI_EXOKAY: fifo_wr_resp.status = JTAG_AXI_EXOKAY;
            AXI_SLVERR: fifo_wr_resp.status = JTAG_AXI_SLVERR;
            AXI_DECERR: fifo_wr_resp.status = JTAG_AXI_DECERR;
          endcase
        end
      end : b_axi
    end

    // In case our resp AFIFO is full, bp the bus on slave answer
    if (fifo_wr_txn_full) begin
      jtag_axi_mosi_o.rready = 1'b0;
      jtag_axi_mosi_o.bready = 1'b0;
    end

    timeout_axi_aw = aw_timeout;
    timeout_axi_ar = ar_timeout;
    timeout_axi_w  = w_timeout;
    timeout_axi_b  = b_timeout;
    timeout_axi_r  = r_timeout;
  end

  always_ff @ (posedge clk or posedge ares) begin
    if (ares) begin
      timeout_axi_aw_ff <= 1'b0;
      timeout_axi_ar_ff <= 1'b0;
      timeout_axi_w_ff  <= 1'b0;
      timeout_axi_b_ff  <= 1'b0;
      timeout_axi_r_ff  <= 1'b0;
    end
    else begin
      timeout_axi_aw_ff <= timeout_axi_aw;
      timeout_axi_ar_ff <= timeout_axi_ar;
      timeout_axi_w_ff  <= timeout_axi_w;
      timeout_axi_b_ff  <= timeout_axi_b;
      timeout_axi_r_ff  <= timeout_axi_r;
    end
  end

  jtag_axi_fifo #(
    .SLOTS    (AXI_ASYNC_FIFO_DEPTH),
    .t_data   (int_op_type_t)
  ) u_axi_fifo_addr_op_seq (
    .clk      (clk),
    .rst      (ares),
    .clear_i  (1'b0),
    .write_i  (fifo_wr_en_addr_op),
    .read_i   (fifo_rd_en_addr_op),
    .data_i   (op_type_in),
    .data_o   (op_type_out),
    .error_o  (),
    .full_o   (fifo_full_addr_op),
    .empty_o  (fifo_empty_addr_op),
    .ocup_o   ()
  );

  jtag_axi_timeout #(
    .TIMEOUT_CLK_CYCLES (AXI_TIMEOUT_CC)
  ) u_aw_timeout (
    .clk      (clk),
    .ares     (ares),
    .valid    (jtag_axi_mosi_o.awvalid),
    .ready    (jtag_axi_miso_i.awready),
    .timeout  (aw_timeout)
  );

  jtag_axi_timeout #(
    .TIMEOUT_CLK_CYCLES (AXI_TIMEOUT_CC)
  ) u_ar_timeout (
    .clk      (clk),
    .ares     (ares),
    .valid    (jtag_axi_mosi_o.arvalid),
    .ready    (jtag_axi_miso_i.arready),
    .timeout  (ar_timeout)
  );

  jtag_axi_timeout #(
    .TIMEOUT_CLK_CYCLES (AXI_TIMEOUT_CC)
  ) u_w_timeout (
    .clk      (clk),
    .ares     (ares),
    .valid    (jtag_axi_mosi_o.wvalid),
    .ready    (jtag_axi_miso_i.wready),
    .timeout  (w_timeout)
  );

  jtag_axi_timeout #(
    .TIMEOUT_CLK_CYCLES (AXI_TIMEOUT_CC)
  ) u_b_timeout (
    .clk      (clk),
    .ares     (ares),
    .valid    (jtag_axi_mosi_o.bready),
    .ready    (jtag_axi_miso_i.bvalid),
    .timeout  (b_timeout)
  );

  jtag_axi_timeout #(
    .TIMEOUT_CLK_CYCLES (AXI_TIMEOUT_CC)
  ) u_r_timeout (
    .clk      (clk),
    .ares     (ares),
    .valid    (jtag_axi_mosi_o.rready),
    .ready    (jtag_axi_miso_i.rvalid),
    .timeout  (r_timeout)
  );

  cdc_2ff_sync u_2ff_timeout_aw (
    .clk_sync    (tck),
    .arst_master (~trstn),
    .async_i     (timeout_axi_aw_ff),
    .sync_o      (timeout_aw_jtag_o)
  );

  cdc_2ff_sync u_2ff_timeout_ar (
    .clk_sync    (tck),
    .arst_master (~trstn),
    .async_i     (timeout_axi_ar_ff),
    .sync_o      (timeout_ar_jtag_o)
  );

  cdc_2ff_sync u_2ff_timeout_w (
    .clk_sync    (tck),
    .arst_master (~trstn),
    .async_i     (timeout_axi_w_ff),
    .sync_o      (timeout_w_jtag_o)
  );

  cdc_2ff_sync u_2ff_timeout_b (
    .clk_sync    (tck),
    .arst_master (~trstn),
    .async_i     (timeout_axi_b_ff),
    .sync_o      (timeout_b_jtag_o)
  );

  cdc_2ff_sync u_2ff_timeout_r (
    .clk_sync    (tck),
    .arst_master (~trstn),
    .async_i     (timeout_axi_r_ff),
    .sync_o      (timeout_r_jtag_o)
  );
endmodule
