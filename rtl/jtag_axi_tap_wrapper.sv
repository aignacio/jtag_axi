/**
 * File              : jtag_axi_tap_wrapper.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 25.08.2024
 * Last Modified Date: 30.09.2024
 */
module jtag_axi_tap_wrapper
  import jtag_axi_pkg::*;
#(
  parameter [31:0]  IDCODE_VAL    = 'hBADC0FFE,
  parameter int     IC_RST_WIDTH  = 4
)(
  input                               trstn,
  input                               tck,
  input                               tms,
  input                               tdi,
  output                              tdo,
  output  logic [(IC_RST_WIDTH-1):0]  ic_rst,
  input   logic [31:0]                usercode_i,
  output  logic                       usercode_update_o,
  // To AXI I/F
  input   s_axi_jtag_status_t         jtag_status_i,
  output  logic                       axi_status_rd_o, // Ack last status
  input   axi_afifo_t                 afifo_slots_i,
  output  s_axi_jtag_info_t           axi_info_o,
  output  logic                       axi_req_new_o // Dispatch a new txn when assert
);
  tap_ctrl_fsm_t    tap_state;
  ir_decoding_t     ir_dec;
  logic             select_dr;
  logic             tdo_ir;
  logic             tdo_dr;

  jtag_axi_tap_ctrl_fsm u_tap_ctrl_fsm (
    .trstn      (trstn),
    .tck        (tck),
    .tms        (tms),
    .tap_state  (tap_state)
  );

  jtag_axi_instruction_register u_instruction_register (
    .trstn      (trstn),
    .tck        (tck),
    .tdi        (tdi),
    .tdo        (tdo_ir),
    .tap_state  (tap_state),
    .ir_dec     (ir_dec),
    .select_dr  (select_dr)
  );

  assign tdo  = (select_dr == 1'b0) ? tdo_ir : tdo_dr;

  jtag_axi_data_registers #(
    .IDCODE_VAL       (IDCODE_VAL),
    .IC_RST_WIDTH     (IC_RST_WIDTH)
  ) u_data_registers (
    .trstn            (trstn),
    .tck              (tck),
    .tdi              (tdi),
    .tdo              (tdo_dr),
    .tap_state        (tap_state),
    .ir_dec           (ir_dec),
    // Data Registers output
    .ic_rst           (ic_rst),
    .usercode_i       (usercode_i),
    .usercode_update_o(usercode_update_o),
    .jtag_status_i    (jtag_status_i),
    .axi_status_rd_o  (axi_status_rd_o),
    .afifo_slots_i    (afifo_slots_i),
    .axi_info_o       (axi_info_o),
    .axi_req_new_o    (axi_req_new_o)
  );
endmodule
