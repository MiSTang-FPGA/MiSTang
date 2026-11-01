// Design B: fast LED chase, never touches RECONFIG_N.
module b(input clk, inout recon, output [5:0] led);
  reg [28:0] c = 0; always @(posedge clk) c <= c + 1;
  assign recon = 1'bz;
  assign led = ~(6'b000001 << c[25:23]);
endmodule
