/**
 * File              : dut.sv
 * License           : MIT license <Check LICENSE>
 * Author            : Anderson I. da Silva (aignacio) <anderson@aignacio.com>
 * Date              : 04.11.2023
 * Last Modified Date: 04.11.2023
 */
module dut #(
  parameter WIDTH = 32
)(
  input                     clk,
  input                     arst,
  output  logic [WIDTH-1:0] data
);
  assign data = 'hDEADBEEF;
endmodule
