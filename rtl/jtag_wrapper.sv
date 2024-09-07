/**
 * File              : jtag_wrapper.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 25.08.2024
 * Last Modified Date: 08.09.2024
 */
module jtag_wrapper
  import jtag_pkg::*;
#(
  parameter [31:0] IDCODE_VAL = 'hBADC0FFE,
  parameter int IC_RST_WIDTH  = 4
)(
  input        trstn,
  input        tck,
  input        tms,
  input        tdi,
  output       tdo,
  output logic addr,
  output logic data
);
  tap_ctrl_fsm_t  tap_state;
  ir_decoding_t   ir_dec;
  logic           select_dr;
  logic           tdo_ir;
  logic           tdo_dr;
  s_axi_jtag_t    axi_info;

  tap_ctrl_fsm u_tap_ctrl_fsm (
    .trstn      (trstn),
    .tck        (tck),
    .tms        (tms),
    .tap_state  (tap_state)
  );

  instruction_register u_instruction_register (
    .trstn      (trstn),
    .tck        (tck),
    .tdi        (tdi),
    .tdo        (tdo_ir),
    .tap_state  (tap_state),
    .ir_dec     (ir_dec),
    .select_dr  (select_dr)
  );

  assign tdo  = (select_dr == 1'b0) ? tdo_ir : tdo_dr;
  assign addr = axi_info.addr[0];
  assign data = axi_info.data_write[0];

  data_registers #(
    .IDCODE_VAL   (IDCODE_VAL),
    .IC_RST_WIDTH (IC_RST_WIDTH)
  ) u_data_registers (
    .trstn      (trstn),
    .tck        (tck),
    .tdi        (tdi),
    .tdo        (tdo_dr),
    .tap_state  (tap_state),
    .ir_dec     (ir_dec),
    // Data Registers output
    .ic_rst     (),
    .axi_info   (axi_info),
    .axi_update ()
  );
endmodule
