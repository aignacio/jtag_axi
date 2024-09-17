/**
 * File              : jtag_axi_if.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 11.09.2024
 * Last Modified Date: 17.09.2024
 */
module jtag_axi_if
  import amba_axi_pkg::*;
  import jtag_axi_pkg::*;
#(
  parameter int AXI_MASTER_ID = 0
)(
  input                         clk,
  input                         ares,
  output  logic                 axi_timeout_o,
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

  logic         fifo_wr_en_addr_op;
  logic         fifo_rd_en_addr_op;
  logic         fifo_empty_addr_op;
  logic         fifo_full_addr_op;
  int_op_type_t op_type_in, op_type_out;

  always_comb begin
    axi_timeout_o = 1'b0;
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

endmodule

