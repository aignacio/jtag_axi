/**
 * File              : data_registers.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 28.08.2024
 * Last Modified Date: 05.09.2024
 */
module data_registers
  import jtag_pkg::*;
#(
  parameter [31:0] IDCODE_VAL = 'h10F,
  parameter int IC_RST_WIDTH  = 4
)(
  input                              trstn,
  input                              tck,
  input                              tdi,
  output  logic                      tdo,
  input   tap_ctrl_fsm_t             tap_state,
  input   ir_decoding_t              ir_dec,
  output  logic [(IC_RST_WIDTH-1):0] ic_rst,
  output  s_axi_jtag_t               axi_info,
  output  logic                      axi_update
);
  logic bypass_ff, next_bypass;
  logic bypass_n_ff;

  logic [31:0] idcode_ff, next_idcode;
  logic [31:0] idcode_n_ff;

  logic [(IC_RST_WIDTH-1):0] ic_rst_ff, next_ic_rst;
  logic [(DR_MAX_WIDTH-1):0] sr_ff, next_sr;
  logic [(DR_MAX_WIDTH-1):0] sr_n_ff;

  s_axi_jtag_t axi_ff, next_axi;

  logic axi_update_ff, next_axi_update;

  always_comb begin
    ic_rst = ic_rst_ff;
    axi_info = axi_ff;
    axi_update = axi_update_ff;
  end

  always_comb begin
    tdo = 1'b0;

    next_axi_update = 1'b0;
    next_bypass = bypass_ff;
    next_idcode = idcode_ff;
    next_ic_rst = ic_rst_ff;
    next_axi = axi_ff;
    next_sr = sr_ff;

    /* verilator lint_off CASEINCOMPLETE */
    unique0 case (ir_dec)
      BYPASS: begin
        // IEEE Std 1149.1-2013 - Section 8.4
        // The bypass register contains a single shift-register stage and is
        // used to provide a minimum-length serial path between the TDI and
        // the TDO pins of a component when no test operation of that compo
        // nent is required. This allows more rapid movement of test data to
        // and from other components on a board that are required to perform
        // test operations.
        if (tap_state == CAPTURE_DR) begin
          next_bypass = 1'b0;
        end
        else if (tap_state == SHIFT_DR) begin
          next_bypass = tdi;
          tdo = bypass_n_ff;
        end
      end
      IDCODE: begin
        // IEEE Std 1149.1-2013 - Section 8.13
        //
        // IDCODE Register (32 bits)
        // +-------+------------------+--------------------+------+
        // | 31:28 |       27:12      |        11:1        | 0    |
        // +-------+------------------+--------------------+------+
        // | Ver   |   Part Number    |  Manufacturer ID   | 1    |
        // | 4-bits|      16-bits     |        11-bits     | 1-bit|
        // +------+------------------+---------------------+------+
        if (tap_state == CAPTURE_DR) begin
          next_idcode = IDCODE_VAL;
        end
        else if (tap_state == SHIFT_DR) begin
          next_idcode = {tdi,idcode_ff[31:1]};
          tdo = idcode_n_ff[0];
        end
      end
      SAMPLE_PRELOAD: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr = '0;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr = {tdi,sr_ff[(DR_MAX_WIDTH-1):1]};
          tdo = sr_n_ff[0];
        end
      end
      IC_RESET: begin
        // IEEE Std 1149.1-2013 - Section 8.4
        // The purpose of the optional IC_RESET instruction is to provide a means 
        // to control reset and related signals to the system logic using the TAP.
        // This instruction selects the reset selection register (see Clause 17)
        // ...
        if (tap_state == CAPTURE_DR) begin
          next_sr[(IC_RST_WIDTH-1):0] = ic_rst_ff;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr[(IC_RST_WIDTH-1):0] = {tdi,sr_ff[(IC_RST_WIDTH-1):1]};
          tdo = sr_n_ff[0];
        end
        else if (tap_state == UPDATE_DR) begin
          next_ic_rst = sr_ff[(IC_RST_WIDTH-1):0];
        end
      end
      ADDR_AXI_REGISTER: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr[(ADDR_AXI_WIDTH-1):0] = axi_ff.addr;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr[(ADDR_AXI_WIDTH-1):0] = {tdi,sr_ff[(ADDR_AXI_WIDTH-1):1]};
          tdo = sr_n_ff[0];
        end
        else if (tap_state == UPDATE_DR) begin
          next_axi.addr = sr_ff[(ADDR_AXI_WIDTH-1):0];
        end
      end
      DATA_AXI_REGISTER: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr[(DATA_AXI_WIDTH-1):0] = axi_ff.data;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr[(DATA_AXI_WIDTH-1):0] = {tdi,sr_ff[(DATA_AXI_WIDTH-1):1]};
          tdo = sr_n_ff[0];
        end
        else if (tap_state == UPDATE_DR) begin
          next_axi.data = sr_ff[(DATA_AXI_WIDTH-1):0];
        end
      end
      MGMT_AXI_REGISTER: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr[(MGMT_WIDTH-1):0] = axi_ff.mgmt.flat;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr[(MGMT_WIDTH-1):0] = {tdi,sr_ff[(MGMT_WIDTH-1):1]};
          tdo = sr_n_ff[0];
        end
        else if (tap_state == UPDATE_DR) begin
          next_axi.mgmt = s_axi_jtag_mgmt_t'(sr_ff);
          next_axi_update = 1'b1;
        end
      end
    endcase
    /* verilator lint_on CASEINCOMPLETE */
  end

  always_ff @ (posedge tck or negedge trstn) begin
    if (trstn == 1'b0) begin
      bypass_ff     <= 1'b0;
      idcode_ff     <= '0;
      sr_ff         <= '0;
      axi_ff        <= s_axi_jtag_t'(0);
      ic_rst_ff     <= '0;
      axi_update_ff <= 1'b0;
    end
    else begin
      bypass_ff     <= next_bypass;
      idcode_ff     <= next_idcode;
      sr_ff         <= next_sr;
      axi_ff        <= next_axi;
      ic_rst_ff     <= next_ic_rst;
      axi_update_ff <= next_axi_update;
    end
  end

  //  IEEE Std 1149.1-2013 - Section 4.5.1
  // a) Changes in the state of the signal driven through TDO shall occur 
  //    only on the falling edge of either TCK or the optional TRST*.
  // b) The TDO driver shall be set to its inactive drive state except 
  //    when the shifting of data is in progress (see 6.1.2).
  always_ff @ (negedge tck or negedge trstn) begin
    if (trstn == 1'b0) begin
      bypass_n_ff <= 1'b0;
      idcode_n_ff <= '0;
      sr_n_ff     <= '0;
    end
    else begin
      bypass_n_ff <= bypass_ff;
      idcode_n_ff <= idcode_ff;
      sr_n_ff     <= sr_ff;
    end
  end

  initial begin
    if (IC_RST_WIDTH > DR_MAX_WIDTH) begin
      $error("IC_RST_WIDTH needs to be <= DR_MAX_WIDTH");
    end
  end
endmodule
