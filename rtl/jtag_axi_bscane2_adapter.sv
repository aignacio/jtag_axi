/**
 * File              : jtag_axi_bscan_adapter.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 13.12.2025
 * Last Modified Date: 13.12.2025
 */
module jtag_axi_bscane2_adapter
  import jtag_axi_pkg::*;
(
  output logic                trstn,
  output logic                tck,
  output logic                tdi,
  input                       tdo,
  output tap_ctrl_fsm_t       tap_state,
  output ir_decoding_t        ir_dec,
  output logic          [1:0] debug_io
);
  // ---------------------
  // DATAPATH BSCANE2 - IR Length: 6bits / IR address: 0x2
  // ---------------------
  logic dp_capture, dp_shift, dp_update;

  always_comb begin
    unique0 case (1)
      dp_capture: tap_state = CAPTURE_DR;
      dp_shift:   tap_state = SHIFT_DR;
      dp_update:  tap_state = UPDATE_DR;
      default:    tap_state = EXIT1_DR;
    endcase
  end

  assign trstn = ~dp_reset;

  BSCANE2 #(
    .JTAG_CHAIN(1)  // Value for USER command.
  ) u_bscane2_datapath (
    .CAPTURE(dp_capture),  // 1-bit output: CAPTURE output from TAP controller.
    .DRCK   (),            // 1-bit output: Gated TCK output. When SEL is asserted, 
    // DRCK toggles when CAPTURE or
    // SHIFT are asserted.
    .RESET  (dp_reset),    // 1-bit output: Reset output for TAP controller.
    .RUNTEST(),            // 1-bit output: Output asserted when TAP controller is in Run Test/Idle state.
    .SEL    (),            // 1-bit output: USER instruction active output.
    .SHIFT  (dp_shift),    // 1-bit output: SHIFT output from TAP controller.
    .TCK    (tck),         // 1-bit output: Test Clock output. Fabric connection to TAP Clock pin.
    .TDI    (tdi),         // 1-bit output: Test Data Input (TDI) output from TAP controller.
    .TMS    (),            // 1-bit output: Test Mode Select output. Fabric connection to TAP.
    .UPDATE (dp_update),   // 1-bit output: UPDATE output from TAP controller
    .TDO    (tdo)          // 1-bit input: Test Data Output (TDO) input for USER function.
  );

  // ---------------------
  // CTRL BSCANE2 - IR Length: 6bits / IR address: 0x3
  // ---------------------
  logic ctrl_drck, ctrl_update, ctrl_shift, ctrl_capture;
  logic ctrl_tdo, ctrl_tdi, ctrl_reset;

  BSCANE2 #(
    .JTAG_CHAIN(2)  // Value for USER command.
  ) u_bscane2_control (
    .CAPTURE(ctrl_capture),  // 1-bit output: CAPTURE output from TAP controller.
    .DRCK   (ctrl_drck),     // 1-bit output: Gated TCK output. When SEL is asserted, 
    // DRCK toggles when CAPTURE or
    // SHIFT are asserted.
    .RESET  (ctrl_reset),    // 1-bit output: Reset output for TAP controller.
    .RUNTEST(),              // 1-bit output: Output asserted when TAP controller is in Run Test/Idle state.
    .SEL    (),              // 1-bit output: USER instruction active output.
    .SHIFT  (ctrl_shift),    // 1-bit output: SHIFT output from TAP controller.
    .TCK    (),              // 1-bit output: Test Clock output. Fabric connection to TAP Clock pin.
    .TDI    (ctrl_tdi),      // 1-bit output: Test Data Input (TDI) output from TAP controller.
    .TMS    (),              // 1-bit output: Test Mode Select output. Fabric connection to TAP.
    .UPDATE (ctrl_update),   // 1-bit output: UPDATE output from TAP controller
    .TDO    (ctrl_tdo)       // 1-bit input: Test Data Output (TDO) input for USER function.
  );

  logic [31:0] jdr_user2_ff;
  logic [31:0] sr_ff, next_sr;
  logic [31:0] sr_n_ff;

  always_comb begin
    next_sr  = sr_ff;
    ctrl_tdo = sr_n_ff[0];
    ir_dec   = ir_decoding_t'(jdr_user2_ff[3:0]);

    if (ctrl_capture) begin
      next_sr = jdr_user2_ff;
    end

    if (ctrl_shift) begin
      next_sr = {tdi, sr_ff[31:1]};
    end
    debug_io = {jdr_user2_ff[31], jdr_user2_ff[0]};
  end

  always_ff @(posedge ctrl_drck or posedge ctrl_reset) begin
    if (ctrl_reset) begin
      jdr_user2_ff <= '0;
      sr_ff        <= '0;
    end
    else begin
      sr_ff        <= next_sr;
      jdr_user2_ff <= ctrl_update ? sr_ff : jdr_user2_ff;
    end
  end

  always_ff @(negedge ctrl_drck or posedge ctrl_reset) begin
    if (ctrl_reset) begin
      sr_n_ff <= '0;
    end
    else begin
      sr_n_ff <= sr_ff;
    end
  end
endmodule
