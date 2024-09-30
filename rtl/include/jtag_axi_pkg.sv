`ifndef __JTAG_AXI_PKG__
  `define __JTAG_AXI_PKG__

package jtag_axi_pkg;
  import amba_axi_pkg::axi_size_t;
  import amba_axi_pkg::axi_addr_t;
  import amba_axi_pkg::axi_data_t;
  import amba_axi_pkg::axi_wr_strb_t;

  localparam AXI_ASYNC_FIFO_DEPTH = 4; // Must be a power of 2

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
    EXTEST          = 'b0000, // TODO: Implement BSD
    SAMPLE_PRELOAD  = 'b1010, // TODO: Implement BSD
    IC_RESET        = 'b1100,
    IDCODE          = 'b1110,
    BYPASS          = 'b1111,
    ADDR_AXI_REG    = 'b0001,
    DATA_W_AXI_REG  = 'b0010,
    WSTRB_AXI_REG   = 'b0011,
    CTRL_AXI_REG    = 'b0100,
    STATUS_AXI_REG  = 'b0101,
    USERCODE        = 'b0111,
    USERDATA        = 'b0110
  } ir_decoding_t;

  // --------------------------
  //|  JTAG AXI structs/types  |
  // --------------------------
  typedef enum logic [3:0] {
    JTAG_IDLE        = 'd0,
    JTAG_RUNNING     = 'd1,
    JTAG_TIMEOUT_AR  = 'd2,
    JTAG_TIMEOUT_R   = 'd3,
    JTAG_TIMEOUT_AW  = 'd4,
    JTAG_TIMEOUT_W   = 'd5,
    JTAG_TIMEOUT_B   = 'd6,
    JTAG_AXI_OKAY    = 'd7,
    JTAG_AXI_EXOKAY  = 'd8,
    JTAG_AXI_SLVERR  = 'd9,
    JTAG_AXI_DECERR  = 'd10
  } axi_jtag_status_t;

  typedef enum logic {
    AXI_READ  = 'd0,
    AXI_WRITE = 'd1
  } axi_jtag_txn_t;

  typedef logic [$clog2(AXI_ASYNC_FIFO_DEPTH):0] axi_afifo_t;

  typedef struct packed {
    axi_data_t        data_rd;
    axi_jtag_status_t status;
  } s_axi_jtag_status_t;

  typedef struct packed {
    logic             start;
    axi_jtag_txn_t    txn_type;
    axi_afifo_t       fifo_ocup;
    axi_size_t        size;
  } s_axi_jtag_ctrl_t;

  typedef struct packed {
    axi_jtag_txn_t    txn_type;
    axi_size_t        size;
    axi_addr_t        addr;
  } s_axi_afifo_to_axi_t;

  typedef struct packed {
    axi_addr_t        addr;
    axi_data_t        data_wr;
    axi_wr_strb_t     wstrb;
    s_axi_jtag_ctrl_t ctrl;
  } s_axi_jtag_info_t;

  `define ERROR_IF(cond,  msg) \
        generate if (cond) \
          $error (msg); \
        endgenerate

endpackage

`endif
