/**
 * File              : jtag_axi_fifo.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson Ignacio da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 16.10.2021
 * Last Modified Date: 14.09.2024
 *
 * Simple FIFO SLOTSxWIDTH with async reads
 */
module jtag_axi_fifo
#(
  parameter int   SLOTS = 2,
  parameter type  t_data = logic
)(
  input                                     clk,
  input                                     rst,
  input                                     clear_i,
  input                                     write_i,
  input                                     read_i,
  input   t_data                            data_i,
  output  t_data                            data_o,
  output  logic                             error_o,
  output  logic                             full_o,
  output  logic                             empty_o,
  output  logic [$clog2(SLOTS>1?SLOTS:2):0] ocup_o
);
  `define MSB_SLOT  $clog2(SLOTS>1?SLOTS:2)

  t_data [SLOTS-1:0] fifo_ff;
  logic [`MSB_SLOT:0] write_ptr_ff;
  logic [`MSB_SLOT:0] read_ptr_ff;
  logic [`MSB_SLOT:0] next_write_ptr;
  logic [`MSB_SLOT:0] next_read_ptr;
  logic [`MSB_SLOT:0] fifo_ocup;

  always_comb begin
    // Separating full/empty computation into another procedure due to verilator UNOPTFLAT
    full_o  = (write_ptr_ff[`MSB_SLOT-1:0] == read_ptr_ff[`MSB_SLOT-1:0]) &&
              (write_ptr_ff[`MSB_SLOT] != read_ptr_ff[`MSB_SLOT]);
    empty_o = (write_ptr_ff == read_ptr_ff);
  end

  always_comb begin
    next_read_ptr = read_ptr_ff;
    next_write_ptr = write_ptr_ff;
    data_o  = empty_o ? t_data'('0) : fifo_ff[read_ptr_ff[`MSB_SLOT-1:0]];

    if (write_i && ~full_o)
      next_write_ptr = write_ptr_ff + 'd1;

    if (read_i && ~empty_o)
      next_read_ptr = read_ptr_ff + 'd1;

    error_o = (write_i && full_o) || (read_i && empty_o);
    fifo_ocup = write_ptr_ff - read_ptr_ff;
    ocup_o = fifo_ocup;

    // Clear has high priority
    if (clear_i) begin
      next_read_ptr = 'd0;
      next_write_ptr = 'd0;
      data_o = t_data'('d0);
      ocup_o = 'd0;
    end
  end

  always_ff @ (posedge clk or posedge rst) begin
    if(rst) begin
      write_ptr_ff <= '0;
      read_ptr_ff <= '0;
      //fifo_ff <= '0;
    end
    else begin
      write_ptr_ff <= next_write_ptr;
      read_ptr_ff <= next_read_ptr;
      if (write_i && ~full_o)
        fifo_ff[write_ptr_ff[`MSB_SLOT-1:0]] <= data_i;
    end
  end

  `ERROR_IF(2**$clog2(SLOTS) != SLOTS, "SLOT must be a power of 2")
  `ERROR_IF(SLOTS < 2, "SLOTS must be equal or greater than 2")

endmodule
