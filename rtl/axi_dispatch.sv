/**
 * File              : axi_dispatch.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 09.09.2024
 * Last Modified Date: 10.09.2024
 */
module axi_dispatch
  import amba_axi_pkg::*;
  import jtag_pkg::*;
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
  output  logic               axi_req_new_o,
  // AXI I/F
  output  s_axi_mosi_t        jtag_axi_mosi_o,
  input   s_axi_miso_t        jtag_axi_miso_i
);
  axi_jtag_status_t st_ff, next_st;
  
  always_comb begin
    jtag_status_o = st_ff;
    next_st = st_ff;

    //unique0 case ()
    //endcase
  end

  always_ff @ (posedge tck or negedge trstn) begin
    if (ares) begin
      st_ff <= JTAG_IDLE;
    end
    else begin
      st_ff <= next_st;
    end
  end

  cdc_async_fifo_w_ocup #(
    .SLOTS  (AXI_ASYNC_FIFO_DEPTH),
    .WIDTH  (32)
  ) u_afifo_jtag_to_axi (
    // JTAG side
    .clk_wr     (tck),
    .arst_wr    (~trstn),
    .wr_en_i    (axi_s),
    .wr_data_i  ('0),
    .wr_full_o  (),
    .ocup_o     (afifo_slots_o),
    // AXI side
    .clk_rd     (clk),
    .arst_rd    (ares),
    .rd_en_i    ('0),
    .rd_data_o  (),
    .rd_empty_o ()
  );
endmodule
