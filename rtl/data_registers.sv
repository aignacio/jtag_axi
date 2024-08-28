/**
 * File              : data_registers.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 28.08.2024
 * Last Modified Date: 28.08.2024
 */
module data_registers
  import jtag_pkg::*;
#(
  parameter [31:0] IDCODE_VAL = 'h10F
)(
  input                   trstn,
  input                   tck,
  input                   tdi,
  output  logic           tdo,
  input   tap_ctrl_fsm_t  tap_state,
  input   ir_decoding_t   ir_dec,
  output  logic [31:0]    addr,
  output  logic [31:0]    data
);
  logic         bypass_ff, next_bypass;
  logic [31:0]  sr_ff, next_sr;
  logic [31:0]  addr_ff, next_addr;
  logic [31:0]  data_wr_ff, next_data_wr;
  logic [31:0]  data_rd_ff, next_data_rd;

  always_comb begin
    addr = addr_ff;
    data = data_wr_ff;
  end

  always_comb begin
    tdo = 1'b0;
    next_addr = addr_ff;
    next_data_wr = data_wr_ff;
    next_data_rd = data_rd_ff;
    next_bypass = bypass_ff;
    next_sr = sr_ff;
    /* verilator lint_off CASEINCOMPLETE */
    unique0 case (ir_dec)
      BYPASS: begin
        if (tap_state == CAPTURE_DR) begin
          next_bypass = 1'b0;
        end
        else if (tap_state == SHIFT_DR) begin
          tdo = bypass_ff;
          next_bypass = tdi;
        end
      end
      IDCODE: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr = IDCODE_VAL;
        end
        else if (tap_state == SHIFT_DR) begin
          tdo = sr_ff[0];
          next_sr = {tdo,sr_ff[31:1]};
        end
      end
      ADDR_REGISTER: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr = addr_ff;
        end
        else if (tap_state == SHIFT_DR) begin
          tdo = sr_ff[0];
          next_sr = {tdi,sr_ff[31:1]};
        end
        else if (tap_state == UPDATE_DR) begin
          next_addr = sr_ff;
        end
      end
      DATA_WR_REGISTER: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr = data_wr_ff;
        end
        else if (tap_state == SHIFT_DR) begin
          tdo = sr_ff[0];
          next_sr = {tdi,sr_ff[31:1]};
        end
        else if (tap_state == UPDATE_DR) begin
          next_data_wr = sr_ff;
        end
      end
      DATA_RD_REGISTER: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr = data_rd_ff;
        end
        else if (tap_state == SHIFT_DR) begin
          tdo = sr_ff[0];
          next_sr = {tdo,sr_ff[31:1]};
        end
        else if (tap_state == UPDATE_DR) begin
          next_data_rd = '0;
        end
      end

    endcase
    /* verilator lint_on CASEINCOMPLETE */
  end

  always_ff @ (posedge tck or negedge trstn) begin
    if (trstn == 1'b0) begin
      bypass_ff <= 1'b0;
      sr_ff     <= '0;
    end
    else begin
      bypass_ff <= next_bypass;
      sr_ff     <= next_sr;
    end
  end

  always_ff @ (negedge tck or negedge trstn) begin
    if (trstn == 1'b0) begin
      addr_ff    <= '0;
      data_wr_ff <= '0;
    end
    else begin
      addr_ff    <= next_addr;
      data_wr_ff <= next_data_wr;
    end
  end
endmodule
