/**
 * File              : jtag_wrapper.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 25.08.2024
 * Last Modified Date: 28.08.2024
 */
module jtag_wrapper
  import jtag_pkg::*;
#(
  parameter [31:0] IDCODE_VAL = 'h10F 
)(
  input                 trstn,
  input                 tck,
  input                 tms,
  input                 tdi,
  output                tdo,
  output  logic [31:0]  addr,
  output  logic [31:0]  data
);
  tap_ctrl_fsm_t  tap_state;
  ir_decoding_t   ir_dec;
  logic           select_dr;
  logic           tdo_ir;
  logic           tdo_dr;

  tap_ctrl_fsm u_tap_ctrl_fsm (
    .trstn      (trstn),
    .tck        (tck),
    .tms        (tms),
    .tap_state  (tap_state)
  );

  instruction_register u_ir (
    .trstn      (trstn),
    .tck        (tck),
    .tdi        (tdi),
    .tdo        (tdo_ir),
    .tap_state  (tap_state),
    .ir_dec     (ir_dec),
    .select_dr  (select_dr)
  );

  assign tdo = (select_dr == 1'b0) ? tdo_ir : tdo_dr;

  data_registers #(
    .IDCODE_VAL (IDCODE_VAL)
  ) u_data_registers (
    .trstn      (trstn),
    .tck        (tck),
    .tdi        (tdi),
    .tdo        (tdo_dr),
    .tap_state  (tap_state),
    .ir_dec     (ir_dec),
    .select_dr  (select_dr),
    // Data Registers output
    .addr       (addr),
    .data       (data)
  );
endmodule
