/**
 * File              : data_registers.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 28.08.2024
 * Last Modified Date: 08.09.2024
 */
module data_registers
  import jtag_pkg::*;
  import amba_axi_pkg::*;
#(
  parameter [31:0] IDCODE_VAL = 'hBADC0FFE, 
  parameter int IC_RST_WIDTH  = 4
)(
  input                              trstn,
  input                              tck,
  input                              tdi,
  output  logic                      tdo,
  input   tap_ctrl_fsm_t             tap_state,
  input   ir_decoding_t              ir_dec,
  // Data Register output
  output  logic [(IC_RST_WIDTH-1):0] ic_rst,
  // To AXI I/F 
  output  s_axi_jtag_t               axi_info,
  output  logic                      axi_status_rd, // Ack last status
  output  logic                      axi_ctrl // Dispatch a new txn when assert
);
  localparam DR_MAX_WIDTH = $bits(s_axi_jtag_ctrl_t);

  logic bypass_ff, next_bypass;
  logic bypass_n_ff;

  logic [31:0] idcode_ff, next_idcode;
  logic [31:0] idcode_n_ff;

  logic [(IC_RST_WIDTH-1):0] ic_rst_ff, next_ic_rst;
  logic [(DR_MAX_WIDTH-1):0] sr_ff, next_sr;
  logic [(DR_MAX_WIDTH-1):0] sr_n_ff;

  s_axi_jtag_t axi_ff, next_axi;

  logic axi_status_rd_ff, next_axi_status_rd;
  logic axi_ctrl_ff, next_axi_ctrl;

  always_comb begin
    ic_rst = ic_rst_ff;
    axi_info = axi_ff;
    axi_status_rd = axi_status_rd_ff;
    axi_ctrl = axi_ctrl_ff;
  end

  always_comb begin
    tdo = 1'b0;

    next_axi_status_rd = 1'b0;
    next_axi_ctrl = 1'b0;
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
      ADDR_AXI_REG: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr[(`AXI_ADDR_WIDTH-1):0] = axi_ff.addr;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr[(`AXI_ADDR_WIDTH-1):0] = {tdi,sr_ff[(`AXI_ADDR_WIDTH-1):1]};
          tdo = sr_n_ff[0];
        end
        else if (tap_state == UPDATE_DR) begin
          next_axi.addr = sr_ff[(`AXI_ADDR_WIDTH-1):0];
        end
      end
      DATA_W_AXI_REG: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr[(`AXI_DATA_WIDTH-1):0] = axi_ff.data_write;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr[(`AXI_DATA_WIDTH-1):0] = {tdi,sr_ff[(`AXI_DATA_WIDTH-1):1]};
          tdo = sr_n_ff[0];
        end
        else if (tap_state == UPDATE_DR) begin
          next_axi.data_write = sr_ff[(`AXI_DATA_WIDTH-1):0];
        end
      end
      CTRL_AXI_REG: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr[($bits(s_axi_jtag_ctrl_t)-1):0] = axi_ff.mgmt.st.control;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr[($bits(s_axi_jtag_ctrl_t)-1):0] = {tdi,sr_ff[($bits(s_axi_jtag_ctrl_t)-1):1]};
          tdo = sr_n_ff[0];
        end
        else if (tap_state == UPDATE_DR) begin
          next_axi.mgmt.st.control = s_axi_jtag_ctrl_t'(sr_ff);
          next_axi_ctrl = 1'b1;
        end
      end
      STATUS_AXI_REG: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr[($bits(axi_jtag_status_t)-1):0] = axi_ff.mgmt.st.status;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr[($bits(axi_jtag_status_t)-1):0] = {tdi,sr_ff[($bits(axi_jtag_status_t)-1):1]};
          tdo = sr_n_ff[0];
        end
        else if (tap_state == UPDATE_DR) begin
          next_axi_status_rd = 1'b1;
        end
      end
    endcase
    /* verilator lint_on CASEINCOMPLETE */
  end

  always_ff @ (posedge tck or negedge trstn) begin
    if (trstn == 1'b0) begin
      bypass_ff        <= 1'b0;
      idcode_ff        <= '0;
      sr_ff            <= '0;
      axi_ff           <= s_axi_jtag_t'(0);
      ic_rst_ff        <= '0;
      axi_status_rd_ff <= 1'b0;
      axi_ctrl_ff      <= 1'b0;
    end
    else begin
      bypass_ff        <= next_bypass;
      idcode_ff        <= next_idcode;
      sr_ff            <= next_sr;
      axi_ff           <= next_axi;
      ic_rst_ff        <= next_ic_rst;
      axi_status_rd_ff <= next_axi_status_rd;
      axi_ctrl_ff      <= next_axi_ctrl;
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
