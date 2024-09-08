/**
 * File              : instruction_register.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 25.08.2024
 * Last Modified Date: 08.09.2024
 */
module instruction_register
  import jtag_pkg::*;
(
  input                   trstn,
  input                   tck,
  input                   tdi,
  output  logic           tdo,
  input   tap_ctrl_fsm_t  tap_state,
  output  ir_decoding_t   ir_dec,
  output  logic           select_dr
);
  localparam MSB_IR_ENC = $bits(ir_decoding_t)-1;
  localparam DEFAULT_FAULT_ISO = 4'b0001;

  ir_decoding_t sr_ff, next_sr;
  ir_decoding_t sr_n_ff;
  ir_decoding_t ir_ff, next_ir;

  always_comb begin
    tdo = 1'b0;
    select_dr = 1'b1;

    next_sr = sr_ff;

    /* verilator lint_off CASEINCOMPLETE */
    unique0 case (tap_state)
      SHIFT_IR: begin
        select_dr = 1'b0;
        // IEEE Std 1149.1-2013 - Section 7.2.1
        //Shift toward serial output
        tdo = sr_n_ff[0];
        next_sr = ir_decoding_t'({tdi,sr_ff[MSB_IR_ENC:1]});
      end
      CAPTURE_IR: begin
        // IEEE Std 1149.1-2013 - Section 7.2.1
        // Load 01 into bits closest to TDO and, optionally, design-specific 
        // data or fixed values into other bits closer to TDI
        next_sr = ir_decoding_t'(DEFAULT_FAULT_ISO);
      end
    endcase
    /* verilator lint_on CASEINCOMPLETE */
  end

  // IEEE Std 1149.1-2013 - Section 7.2.1
  // c) All operations of shift-register stages shall occur on the rising edge
  // of TCK after entry into a controller state.
  always_ff @ (posedge tck or negedge trstn) begin
    if (trstn == 1'b0) begin
      sr_ff <= IDCODE;
    end
    else begin
      sr_ff <= next_sr;
    end
  end

  always_comb begin
    ir_dec = ir_ff;
    next_ir = ir_ff;

    /* verilator lint_off CASEINCOMPLETE */
    unique0 case (tap_state)
      UPDATE_IR: begin
        // IEEE Std 1149.1-2013 - Section 7.2.1
        //7.2.1 d) The data present at the parallel output of the instruction
        //register shall be latched from the shift-register stage on the falling
        //edge of TCK in the Update-IR controller state.
        next_ir = sr_ff;
      end
      TEST_LOGIC_RESET: begin
        // IEEE Std 1149.1-2013 - Section 7.2.1
        //e) After entry into the Test-Logic-Reset controller state as a result
        //of the clocked operation of the TAP controller, the IDCODE instruction
        //(or, if there is no device identification register, the BYPASS
        //instruction) shall be latched onto the instruction register output on
        //the falling edge of TCK.
        next_ir = IDCODE;
      end
    endcase
    /* verilator lint_on CASEINCOMPLETE */
  end

  always_ff @ (negedge tck or negedge trstn) begin
    if (trstn == 1'b0) begin
      // IEEE Std 1149.1-2013 - Section 7.2.1
      //f) If the TRST* input is provided and a low signal is applied to the
      //input, the latched instruction shall change asynchronously to IDCODE
      //(or, if no device identification register is provided, to BYPASS).
      ir_ff   <= IDCODE;
      //  IEEE Std 1149.1-2013 - Section 4.5.1
      // a) Changes in the state of the signal driven through TDO shall occur 
      //    only on the falling edge of either TCK or the optional TRST*.
      // b) The TDO driver shall be set to its inactive drive state except 
      //    when the shifting of data is in progress (see 6.1.2).
      sr_n_ff <= IDCODE;
    end
    else begin
      ir_ff   <= next_ir;
      sr_n_ff <= sr_ff;
    end
  end
endmodule
