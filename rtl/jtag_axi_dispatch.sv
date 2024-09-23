/**
 * File              : jtag_axi_dispatch.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 09.09.2024
 * Last Modified Date: 23.09.2024
 */
module jtag_axi_dispatch
  import amba_axi_pkg::*;
  import jtag_axi_pkg::*;
#(
  parameter int AXI_MASTER_ID  = 0,
  parameter int AXI_TIMEOUT_CC = 4096 
)(
  input                       clk,
  input                       ares,
  input                       tck,
  input                       trstn,
  // To AXI I/F
  output  s_axi_jtag_status_t jtag_status_o,
  input   logic               axi_status_rd_i,
  output  axi_afifo_t         afifo_slots_o,
  input   s_axi_jtag_info_t   axi_info_i,
  input                       axi_req_new_i,
  // AXI I/F
  output  s_axi_mosi_t        jtag_axi_mosi_o,
  input   s_axi_miso_t        jtag_axi_miso_i
);
  s_axi_afifo_to_axi_t  jtag_fifo_in;
  axi_afifo_t           jtag_fifo_slots;
  logic                 jtag_fifo_wr_full;
  s_axi_jtag_status_t   jtag_fifo_resp;
  logic                 jtag_fifo_resp_empty;
  logic                 jtag_fifo_rd;
  logic                 jtag_axi_timeout_aw;
  logic                 jtag_axi_timeout_ar;
  logic                 jtag_axi_timeout_w;
  logic                 jtag_axi_timeout_b;
  logic                 jtag_axi_timeout_r;
  logic                 jtag_req_new;
  logic                 jtag_req_wr_data;
  logic                 axi_afifo_rd_txn_empty;
  s_axi_afifo_to_axi_t  axi_afifo_rd_txn;
  logic                 axi_afifo_rd_en;
  logic                 axi_afifo_wr_en;
  s_axi_jtag_status_t   axi_afifo_wr_resp;
  logic                 axi_afifo_wr_txn_full;
  axi_data_t            axi_afifo_wr_data;
  axi_wr_strb_t         axi_afifo_wr_strb;
  logic                 axi_afifo_wr_data_rd_en;
  logic                 axi_afifo_wr_data_empty;
  axi_afifo_t           ot_cnt_ff, next_ot_cnt;

  always_comb begin
    afifo_slots_o = jtag_fifo_slots;
    jtag_req_new = axi_req_new_i &&
                   axi_info_i.ctrl.start;
    jtag_req_wr_data = axi_req_new_i &&
                       axi_info_i.ctrl.start &&
                       axi_info_i.ctrl.txn_type;
    jtag_fifo_rd = axi_status_rd_i;

    jtag_fifo_in.txn_type = axi_info_i.ctrl.txn_type;
    jtag_fifo_in.size = axi_info_i.ctrl.size;
    jtag_fifo_in.addr = axi_info_i.addr;

    case (1'b1)
      (jtag_axi_timeout_aw): begin
        jtag_status_o.status = JTAG_TIMEOUT_AW;
        jtag_status_o.data_rd = axi_data_t'('0);
      end
      (jtag_axi_timeout_ar): begin
        jtag_status_o.status = JTAG_TIMEOUT_AR;
        jtag_status_o.data_rd = axi_data_t'('0);
      end
      (jtag_axi_timeout_w): begin
        jtag_status_o.status = JTAG_TIMEOUT_W;
        jtag_status_o.data_rd = axi_data_t'('0);
      end
      (jtag_axi_timeout_b): begin
        jtag_status_o.status = JTAG_TIMEOUT_B;
        jtag_status_o.data_rd = axi_data_t'('0);
      end
      (jtag_axi_timeout_r): begin
        jtag_status_o.status = JTAG_TIMEOUT_R;
        jtag_status_o.data_rd = axi_data_t'('0);
      end
      (~jtag_fifo_resp_empty): begin
        jtag_status_o.status  = jtag_fifo_resp.status;
        jtag_status_o.data_rd = jtag_fifo_resp.data_rd;
      end
      (ot_cnt_ff > 0): begin
        jtag_status_o.status = JTAG_RUNNING;
        jtag_status_o.data_rd = axi_data_t'('0);
      end
      default: begin
        jtag_status_o.status  = JTAG_IDLE;
        jtag_status_o.data_rd = axi_data_t'('0);
      end
    endcase
  end

  always_comb begin
    next_ot_cnt = ot_cnt_ff + ((jtag_req_new & ~jtag_fifo_wr_full) ? 'd1 : 'd0) -
                              ((jtag_fifo_rd & ~jtag_fifo_resp_empty) ? 'd1 : 'd0);
  end

  always_ff @ (posedge tck or negedge trstn) begin
    if (~trstn) begin
      ot_cnt_ff <= axi_afifo_t'('0);
    end
    else begin
      ot_cnt_ff <= next_ot_cnt;
    end
  end

  cdc_async_fifo_w_ocup #(
    .SLOTS      (AXI_ASYNC_FIFO_DEPTH),
    .WIDTH      ($bits(s_axi_afifo_to_axi_t))
  ) u_afifo_control_axi (
    // JTAG side
    .clk_wr     (tck),
    .arst_wr    (~trstn),
    .wr_en_i    (jtag_req_new),
    .wr_data_i  (jtag_fifo_in),
    .wr_full_o  (jtag_fifo_wr_full),
    .ocup_o     (jtag_fifo_slots),
    // AXI side
    .clk_rd     (clk),
    .arst_rd    (ares),
    .rd_en_i    (axi_afifo_rd_en),
    .rd_data_o  (axi_afifo_rd_txn),
    .rd_empty_o (axi_afifo_rd_txn_empty)
  );

  localparam W_CH_WIDTH = $bits(axi_data_t) + $bits(axi_wr_strb_t);

  cdc_async_fifo_w_ocup #(
    .SLOTS      (AXI_ASYNC_FIFO_DEPTH),
    .WIDTH      (W_CH_WIDTH)
  ) u_afifo_axi_wdata (
    // JTAG side
    .clk_wr     (tck),
    .arst_wr    (~trstn),
    .wr_en_i    (jtag_req_wr_data),
    .wr_data_i  ({axi_info_i.data_wr, axi_info_i.wstrb}),
    .wr_full_o  (),
    .ocup_o     (),
    // AXI side
    .clk_rd     (clk),
    .arst_rd    (ares),
    .rd_en_i    (axi_afifo_wr_data_rd_en),
    .rd_data_o  ({axi_afifo_wr_data, axi_afifo_wr_strb}),
    .rd_empty_o (axi_afifo_wr_data_empty)
  );

  cdc_async_fifo_w_ocup #(
    .SLOTS      (AXI_ASYNC_FIFO_DEPTH),
    .WIDTH      ($bits(s_axi_jtag_status_t))
  ) u_afifo_resp_axi (
    // AXI side
    .clk_wr     (clk),
    .arst_wr    (ares),
    .wr_en_i    (axi_afifo_wr_en),
    .wr_data_i  (axi_afifo_wr_resp),
    .wr_full_o  (axi_afifo_wr_txn_full),
    .ocup_o     (),
    // JTAG side
    .clk_rd     (tck),
    .arst_rd    (~trstn),
    .rd_en_i    (jtag_fifo_rd),
    .rd_data_o  (jtag_fifo_resp),
    .rd_empty_o (jtag_fifo_resp_empty)
  );

  jtag_axi_if #(
    .AXI_MASTER_ID          (AXI_MASTER_ID),
    .AXI_TIMEOUT_CC         (AXI_TIMEOUT_CC)
  ) u_jtag_axi_if (
    .tck                    (tck),
    .trstn                  (trstn),
    .clk                    (clk),
    .ares                   (ares),
    .timeout_aw_jtag_o      (jtag_axi_timeout_aw),
    .timeout_ar_jtag_o      (jtag_axi_timeout_ar),
    .timeout_w_jtag_o       (jtag_axi_timeout_w),
    .timeout_b_jtag_o       (jtag_axi_timeout_b),
    .timeout_r_jtag_o       (jtag_axi_timeout_r),
    // JTAG to AXI - CTRL signals
    .fifo_rd_txn_empty      (axi_afifo_rd_txn_empty),
    .fifo_rd_txn            (axi_afifo_rd_txn),
    .fifo_rd_en             (axi_afifo_rd_en),
    // JTAG to AXI - Wr data
    .fifo_wr_data_txn_empty (axi_afifo_wr_data_empty),
    .fifo_wr_data           (axi_afifo_wr_data),
    .fifo_wr_strb           (axi_afifo_wr_strb),
    .fifo_wr_data_en        (axi_afifo_wr_data_rd_en),
    // AXI to JTAG - Resp
    .fifo_wr_txn_full       (axi_afifo_wr_txn_full),
    .fifo_wr_resp           (axi_afifo_wr_resp),
    .fifo_wr_en             (axi_afifo_wr_en),
    // AXI Master I/F
    .jtag_axi_mosi_o        (jtag_axi_mosi_o),
    .jtag_axi_miso_i        (jtag_axi_miso_i)
  );

endmodule
