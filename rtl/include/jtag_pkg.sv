`ifndef __JTAG_PKG__
  `define __JTAG_PKG__

package jtag_pkg;

  typedef enum logic [3:0] {
    TEST_LOGIC_RESET  = 'd0,
    RUN_TEST_IDLE     = 'd1,
    SELECT_DR_SCAN    = 'd2,
    CAPTURE_DR        = 'd3,
    SHIFT_DR          = 'd4,
    EXIT1_DR          = 'd5,
    PAUSE_DR          = 'd6,
    EXIT2_DR          = 'd7,
    UPDATE_DR         = 'd8,
    SELECT_IR_SCAN    = 'd9,
    CAPTURE_IR        = 'd10,
    SHIFT_IR          = 'd11,
    EXIT1_IR          = 'd12,
    PAUSE_IR          = 'd13,
    EXIT2_IR          = 'd14,
    UPDATE_IR         = 'd15
  } tap_ctrl_fsm_t;

  typedef enum logic [3:0] {
    EXTEST            = 'b0000,
    DEFAULT_FAULT_ISO = 'b0001,
    DATA_RD_REGISTER  = 'b0011,
    DATA_WR_REGISTER  = 'b0010,
    SAMPLE_PRELOAD    = 'b1010,
    IC_RESET          = 'b1100,
    ADDR_REGISTER     = 'b1101,
    IDCODE            = 'b1110,
    BYPASS            = 'b1111
  } ir_decoding_t;

  localparam MSB_IR_ENC = $bits(ir_decoding_t)-1;

  //typedef struct package {
  //  logic tck;
  //  logic tms;
  //  logic tdi;
  //  logic trst;
  //} s_jtag_mosi_t;

  //typedef struct package {
  //  logic tdo;
  //} s_jtag_miso_t;

endpackage

`endif
