/**
 * File              : jtag_axi_timeout.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 18.09.2024
 * Last Modified Date: 18.09.2024
 */
module jtag_axi_timeout
  import amba_axi_pkg::*;
#(
  parameter int TIMEOUT_CLK_CYCLES = 4096
)(
  input         clk,
  input         ares,
  input         valid,
  input         ready,
  output  logic timeout
);
  typedef logic [$clog2(TIMEOUT_CLK_CYCLES)-1:0] to_t;
  to_t cnt_ff, next_cnt;

  always_comb begin
    next_cnt = cnt_ff;

    if (valid & ~ready && (cnt_ff < to_t'(TIMEOUT_CLK_CYCLES-1))) begin
      next_cnt = cnt_ff + 'd1;
    end
    else if (valid & ready) begin
      next_cnt = 'd0;
    end

    timeout = 1'b0;

    if (cnt_ff == to_t'(TIMEOUT_CLK_CYCLES-1)) begin
      timeout = 1'b1;
    end
  end

  always_ff @ (posedge clk or posedge ares) begin
    if (ares) begin
      cnt_ff <= '0;
    end
    else begin
      cnt_ff <= next_cnt;
    end
  end
endmodule
