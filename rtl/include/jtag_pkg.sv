`ifndef __JTAG_PKG__
  `define __JTAG_PKG__

package jtag_pkg;

  typedef enum logic [3:0] {
    TEST_LOGIC_RESET,
    RUN_TEST_IDLE,
    SELECT_DR_SCAN,
    CAPTURE_DR,
    SHIFT_DR,
    EXIT1_DR,
    PAUSE_DR,
    EXIT2_DR,
    UPDATE_DR,
    SELECT_IR_SCAN,
    CAPTURE_IR,
    SHIFT_IR,
    EXIT1_IR,
    PAUSE_IR,
    EXIT2_IR,
    UPDATE_IR
  } tap_ctrl_fsm_t;
 
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
