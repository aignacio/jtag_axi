/**
 * File              : jtag_axi_data_registers.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 28.08.2024
 * Last Modified Date: 30.09.2024
 */
module jtag_axi_data_registers
  import jtag_axi_pkg::*;
  import amba_axi_pkg::*;
#(
  parameter [31:0]  IDCODE_VAL    = 'hBADC0FFE,
  parameter int     IC_RST_WIDTH  = 4
)(
  input                               trstn,
  input                               tck,
  input                               tdi,
  output  logic                       tdo,
  input   tap_ctrl_fsm_t              tap_state,
  input   ir_decoding_t               ir_dec,
  // Data Register output/input
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
  // Needs to be the largest DR...
  localparam DR_MAX_WIDTH = ($bits(s_axi_jtag_status_t) > $bits(axi_addr_t)) ?
                            $bits(s_axi_jtag_status_t) : $bits(axi_addr_t); 

  logic bypass_ff, next_bypass;
  logic bypass_n_ff;

  logic [31:0] idcode_ff, next_idcode;
  logic [31:0] idcode_n_ff;

  logic [(IC_RST_WIDTH-1):0] ic_rst_ff, next_ic_rst;
  logic [(DR_MAX_WIDTH-1):0] sr_ff, next_sr;
  logic [(DR_MAX_WIDTH-1):0] sr_n_ff;

  s_axi_jtag_info_t axi_info_ff, next_axi_info;

  logic axi_status_rd_ff, next_axi_status_rd;
  logic axi_req_ff, next_axi_req;

  always_comb begin
    ic_rst = ic_rst_ff;
    axi_info_o = axi_info_ff;
    axi_status_rd_o = axi_status_rd_ff;
    axi_req_new_o = axi_req_ff;
  end

  always_comb begin
    tdo = 1'b0;

    usercode_update_o = 1'b0;
    next_axi_status_rd = 1'b0;
    next_axi_req = 1'b0;
    next_bypass = bypass_ff;
    next_idcode = idcode_ff;
    next_ic_rst = ic_rst_ff;
    next_axi_info = axi_info_ff;
    next_axi_info.ctrl.fifo_ocup = afifo_slots_i;
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
        else if (tap_state == EXIT1_DR) begin
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
        else if (tap_state == EXIT1_DR) begin
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
        else if (tap_state == EXIT1_DR) begin
          tdo = sr_n_ff[0];
        end
      end
      USERCODE: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr[31:0] = usercode_i;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr[31:0] = {tdi,sr_ff[31:1]};
          tdo = sr_n_ff[0];
        end
        else if (tap_state == UPDATE_DR) begin
          usercode_update_o = 1'b1;
        end
        else if (tap_state == EXIT1_DR) begin
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
        else if (tap_state == EXIT1_DR) begin
          tdo = sr_n_ff[0];
        end
      end
      ADDR_AXI_REG: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr[(`AXI_ADDR_WIDTH-1):0] = axi_info_ff.addr;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr[(`AXI_ADDR_WIDTH-1):0] = {tdi,sr_ff[(`AXI_ADDR_WIDTH-1):1]};
          tdo = sr_n_ff[0];
        end
        else if (tap_state == UPDATE_DR) begin
          next_axi_info.addr = sr_ff[(`AXI_ADDR_WIDTH-1):0];
        end
        else if (tap_state == EXIT1_DR) begin
          tdo = sr_n_ff[0];
        end
      end
      DATA_W_AXI_REG: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr[(`AXI_DATA_WIDTH-1):0] = axi_info_ff.data_wr;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr[(`AXI_DATA_WIDTH-1):0] = {tdi,sr_ff[(`AXI_DATA_WIDTH-1):1]};
          tdo = sr_n_ff[0];
        end
        else if (tap_state == UPDATE_DR) begin
          next_axi_info.data_wr = sr_ff[(`AXI_DATA_WIDTH-1):0];
        end
        else if (tap_state == EXIT1_DR) begin
          tdo = sr_n_ff[0];
        end
      end
      WSTRB_AXI_REG: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr[((`AXI_DATA_WIDTH/8)-1):0] = axi_info_ff.wstrb;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr[((`AXI_DATA_WIDTH/8)-1):0] = {tdi,sr_ff[((`AXI_DATA_WIDTH/8)-1):1]};
          tdo = sr_n_ff[0];
        end
        else if (tap_state == UPDATE_DR) begin
          next_axi_info.wstrb = sr_ff[((`AXI_DATA_WIDTH/8)-1):0];
        end
        else if (tap_state == EXIT1_DR) begin
          tdo = sr_n_ff[0];
        end
      end
      CTRL_AXI_REG: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr[($bits(s_axi_jtag_ctrl_t)-1):0] = axi_info_ff.ctrl;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr[($bits(s_axi_jtag_ctrl_t)-1):0] = {tdi,sr_ff[($bits(s_axi_jtag_ctrl_t)-1):1]};
          tdo = sr_n_ff[0];
        end
        else if (tap_state == UPDATE_DR) begin
          next_axi_info.ctrl = s_axi_jtag_ctrl_t'(sr_ff);
          next_axi_req = next_axi_info.ctrl.start;
        end
        else if (tap_state == EXIT1_DR) begin
          tdo = sr_n_ff[0];
        end
      end
      STATUS_AXI_REG: begin
        if (tap_state == CAPTURE_DR) begin
          next_sr[($bits(s_axi_jtag_status_t)-1):0] = jtag_status_i;
        end
        else if (tap_state == SHIFT_DR) begin
          next_sr[($bits(s_axi_jtag_status_t)-1):0] = {tdi,sr_ff[($bits(s_axi_jtag_status_t)-1):1]};
          tdo = sr_n_ff[0];
        end
        else if (tap_state == UPDATE_DR) begin
          next_axi_status_rd = 1'b1;
        end
        else if (tap_state == EXIT1_DR) begin
          tdo = sr_n_ff[0];
        end
      end
    endcase
    /* verilator lint_on CASEINCOMPLETE */
  end

  always_ff @ (posedge tck or negedge trstn) begin
    if (trstn == 1'b0) begin
      bypass_ff           <= 1'b0;
      idcode_ff           <= '0;
      sr_ff               <= '0;
      axi_info_ff.addr    <= axi_addr_t'('0);
      axi_info_ff.data_wr <= axi_data_t'('0);
      axi_info_ff.wstrb   <= '1;
      axi_info_ff.ctrl    <= s_axi_jtag_ctrl_t'('0);
      ic_rst_ff           <= '0;
      axi_status_rd_ff    <= 1'b0;
      axi_req_ff          <= 1'b0;
    end
    else begin
      bypass_ff           <= next_bypass;
      idcode_ff           <= next_idcode;
      sr_ff               <= next_sr;
      axi_info_ff         <= next_axi_info;
      ic_rst_ff           <= next_ic_rst;
      axi_status_rd_ff    <= next_axi_status_rd;
      axi_req_ff          <= next_axi_req;
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

  `ERROR_IF(IC_RST_WIDTH>DR_MAX_WIDTH, "Illegal values for parameters \
                                        IC_RST_WIDTH and DR_MAX_WIDTH")
endmodule
