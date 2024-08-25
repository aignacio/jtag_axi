/**
 * File              : tap_ctrl_fsm.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 04.11.2023
 * Last Modified Date: 04.11.2023
 */
module tap_ctrl_fsm 
  import jtag_pkg::*;
(
  input                 trstn,
  input                 tck,
  input                 tms,
  input                 tdi,
  output logic          tdo,
  output tap_ctrl_fsm_t tap_state
);
  tap_ctrl_fsm_t fsm_ff, next_fsm;

  always_comb  begin
    tap_state = fsm_ff;
    tdo = 1'b0;
  end

  always_comb begin
    next_fsm = fsm_ff;

    unique case (fsm_ff)
      TEST_LOGIC_RESET: begin
        if (tms == 1'b0) begin
          next_fsm = RUN_TEST_IDLE;
        end
      end
      RUN_TEST_IDLE: begin
        if (tms == 1'b1) begin
          next_fsm = SELECT_DR_SCAN;
        end
      end
      SELECT_DR_SCAN: begin
        if (tms == 1'b0) begin
          next_fsm = CAPTURE_DR;
        end
        else begin
          next_fsm = SELECT_IR_SCAN;
        end
      end
      CAPTURE_DR: begin
        if (tms == 1'b0) begin
          next_fsm = SHIFT_DR;
        end
        else begin
          next_fsm = EXIT1_DR;
        end
      end
      SHIFT_DR: begin
        if (tms == 1'b1) begin
          next_fsm = EXIT1_DR;
        end
      end
      EXIT1_DR: begin
        if (tms == 1'b0) begin
          next_fsm = PAUSE_DR;
        end
        else begin
          next_fsm = UPDATE_DR;
        end
      end
      PAUSE_DR: begin
        if (tms == 1'b1) begin
          next_fsm = EXIT2_DR;
        end
      end
      EXIT2_DR: begin
        if (tms == 1'b0) begin
          next_fsm = SHIFT_DR;
        end
        else begin
          next_fsm = UPDATE_DR;
        end
      end
      UPDATE_DR: begin
        if (tms == 1'b0) begin
          next_fsm = RUN_TEST_IDLE;
        end
        else begin
          next_fsm = SELECT_DR_SCAN;
        end
      end
      SELECT_IR_SCAN: begin
        if (tms == 1'b1) begin
          next_fsm = TEST_LOGIC_RESET;
        end
        else begin
          next_fsm = CAPTURE_IR;
        end
      end
      CAPTURE_IR: begin
        if (tms == 1'b0) begin
          next_fsm = SHIFT_IR;
        end
        else begin
          next_fsm = EXIT1_IR;
        end
      end
      SHIFT_IR: begin
        if (tms == 1'b1) begin
          next_fsm = EXIT1_IR;
        end
      end
      EXIT1_IR: begin
        if (tms == 1'b1) begin
          next_fsm = UPDATE_IR;
        end
        else begin
          next_fsm = PAUSE_IR;
        end
      end
      PAUSE_IR: begin
        if (tms == 1'b1) begin
          next_fsm = EXIT2_IR;
        end
      end
      EXIT2_IR: begin
        if (tms == 1'b0) begin
          next_fsm = SHIFT_IR;
        end
        else begin
          next_fsm = UPDATE_IR;
        end
      end
      UPDATE_IR: begin
        if (tms == 1'b1) begin
          next_fsm = SELECT_DR_SCAN;
        end
        else begin
          next_fsm = RUN_TEST_IDLE;
        end
      end
    endcase
  end

  always_ff @ (posedge tck or negedge trstn) begin
    if (trstn == 1'b0) begin
      fsm_ff <= TEST_LOGIC_RESET;
    end
    else begin
      fsm_ff <= next_fsm;
    end
  end
endmodule
