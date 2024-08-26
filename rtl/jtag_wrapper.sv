/**
 * File              : jtag_wrapper.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 25.08.2024
 * Last Modified Date: 26.08.2024
 */
module jtag_wrapper
  import jtag_pkg::*;
(
  input                 trstn,
  input                 tck,
  input                 tms,
  input                 tdi,
  output                tdo
);
  tap_ctrl_fsm_t  tap_state;
  ir_decoding_t   ir_dec;

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
    .tdo        (tdo),
    .tap_state  (tap_state),
    .ir_dec     (ir_dec)
  );
endmodule
