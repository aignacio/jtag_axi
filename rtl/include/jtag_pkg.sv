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
    EXTEST         = 'b0000, // TODO: Implement BSD
    SAMPLE_PRELOAD = 'b1010, // TODO: Implement BSD
    IC_RESET       = 'b1100,
    IDCODE         = 'b1110,
    BYPASS         = 'b1111,
    ADDR_AXI_REG   = 'b0001,
    DATA_W_AXI_REG = 'b0010,
    DATA_R_AXI_REG = 'b0011,
    CTRL_AXI_REG   = 'b0100,
    STATUS_AXI_REG = 'b0101
  } ir_decoding_t;

  // --------------------------
  //|  JTAG AXI structs/types  |
  // --------------------------
  typedef enum logic [2:0] {
    JTAG_IDLE        = 'd0,
    JTAG_RUNNING     = 'd1,
    JTAG_TIMEOUT     = 'd2,
    JTAG_AXI_OKAY    = 'd3,
    JTAG_AXI_EXOKAY  = 'd4,
    JTAG_AXI_SLVERR  = 'd5,
    JTAG_AXI_DECERR  = 'd6
  } axi_jtag_status_t;

  typedef enum logic {
    AXI_READ  = 'd0,
    AXI_WRITE = 'd1
  } axi_jtag_txn_t;

  typedef struct packed {
    logic          start;
    axi_jtag_txn_t txn_type;
  } s_axi_jtag_ctrl_t;

  typedef struct packed {
    s_axi_jtag_ctrl_t control;
    axi_jtag_status_t status;
  } s_axi_jtag_mgmt_t;

  localparam MGMT_WIDTH = $bits(s_axi_jtag_mgmt_t);
  localparam ADDR_AXI_WIDTH = 32;
  localparam DATA_AXI_WIDTH = 64;

  typedef union packed {
    logic [(MGMT_WIDTH-1):0] flat;
    s_axi_jtag_mgmt_t        st; 
  } s_axi_jtag_mgmt_ut;

  typedef struct packed {
    logic [(ADDR_AXI_WIDTH-1):0] addr;
    logic [(DATA_AXI_WIDTH-1):0] data_write;
    logic [(DATA_AXI_WIDTH-1):0] data_read;
    s_axi_jtag_mgmt_ut           mgmt;
  } s_axi_jtag_t;

  localparam DEFAULT_FAULT_ISO = 4'b0001;
  localparam MSB_IR_ENC = $bits(ir_decoding_t)-1;
  localparam DR_MAX_WIDTH = ADDR_AXI_WIDTH > DATA_AXI_WIDTH ? ADDR_AXI_WIDTH :
                                                              DATA_AXI_WIDTH;

  //typedef struct packed {
  //  logic tck;
  //  logic tms;
  //  logic tdi;
  //  logic trst;
  //} s_jtag_mosi_t;

  //typedef struct packed {
  //  logic tdo;
  //} s_jtag_miso_t;

endpackage

`endif
