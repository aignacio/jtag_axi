/**
 * File              : jtag_axi_dispatch.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 09.09.2024
 * Last Modified Date: 11.09.2024
 */
module jtag_axi_dispatch
  import amba_axi_pkg::*;
  import jtag_axi_pkg::*;
(
  input                       clk,
  input                       ares,
  input                       tck,
  input                       trstn,
  // To AXI I/F
  output  s_axi_jtag_status_t jtag_status_o,
  input   logic               axi_status_rd_i, // Ack last status
  output  axi_afifo_t         afifo_slots_o,
  input   s_axi_jtag_info_t   axi_info_i, 
  input                       axi_req_new_i,
  // AXI I/F
  output  s_axi_mosi_t        jtag_axi_mosi_o,
  input   s_axi_miso_t        jtag_axi_miso_i
);
  //axi_jtag_status_t st_ff, next_st;

  typedef struct packed {
    logic           start;
    axi_jtag_txn_t  txn_type;
    axi_size_t      size;
  } s_axi_afifo_ctrl_t;

  s_axi_afifo_ctrl_t jtag_fifo_in;
  axi_afifo_t        jtag_afifo_slots;

  logic        jtag_req_new;

  s_axi_jtag_status_t jtag_fifo_resp;
  logic jtag_fifo_resp_empty;
  logic jtag_axi_timeout;
  logic jtag_fifo_rd;

  always_comb begin
    afifo_slots_o = jtag_afifo_slots;
    jtag_req_new = axi_req_new_i;
    jtag_fifo_rd = axi_status_rd_i;

    jtag_fifo_in.start = axi_info_i.ctrl.start;
    jtag_fifo_in.txn_type = axi_info_i.ctrl.txn_type;
    jtag_fifo_in.size = axi_info_i.ctrl.size;

    case (1'b1)
      (jtag_axi_timeout == 1'b1): begin
        jtag_status_o.status = JTAG_TIMEOUT;
        jtag_status_o.data_rd = axi_data_t'('0);
      end
      (~jtag_fifo_resp_empty): begin
        jtag_status_o.status  = jtag_fifo_resp.status;
        jtag_status_o.data_rd = jtag_fifo_resp.data_rd;
      end
      (jtag_afifo_slots > 0): begin
        jtag_status_o.status = JTAG_RUNNING;
        jtag_status_o.data_rd = axi_data_t'('0);
      end
      default: begin
        jtag_status_o.status  = JTAG_IDLE;
        jtag_status_o.data_rd = axi_data_t'('0);
      end
    endcase
  end

  cdc_async_fifo_w_ocup #(
    .SLOTS  (AXI_ASYNC_FIFO_DEPTH),
    .WIDTH  ($bits(s_axi_afifo_ctrl_t))
  ) u_afifo_jtag_to_axi (
    // JTAG side
    .clk_wr     (tck),
    .arst_wr    (~trstn),
    .wr_en_i    (jtag_req_new),
    .wr_data_i  (jtag_fifo_in),
    .wr_full_o  (),
    .ocup_o     (jtag_afifo_slots),
    // AXI side
    .clk_rd     (clk),
    .arst_rd    (ares),
    .rd_en_i    (),
    .rd_data_o  (),
    .rd_empty_o ()
  );

  cdc_async_fifo_w_ocup #(
    .SLOTS  (AXI_ASYNC_FIFO_DEPTH),
    .WIDTH  ($bits(s_axi_jtag_status_t))
  ) u_afifo_axi_to_jtag (
    // JTAG side
    .clk_wr     (clk),
    .arst_wr    (ares),
    .wr_en_i    (),
    .wr_data_i  (),
    .wr_full_o  (),
    .ocup_o     (),
    // AXI side
    .clk_rd     (tck),
    .arst_rd    (~trstn),
    .rd_en_i    (jtag_fifo_rd),
    .rd_data_o  (jtag_fifo_resp),
    .rd_empty_o (jtag_fifo_resp_empty)
  );
endmodule
