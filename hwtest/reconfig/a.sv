// Design A: after ~5 s pull RECONFIG_N (pin 9) low. LEDs: slow blink.
module a(input clk, inout recon, output [5:0] led);
  reg [28:0] c = 0; always @(posedge clk) c <= c + 1;
  wire fire = c[27] & c[26];           // ~ 4.97 s after start, stays for ~2.5 s
  assign recon = fire ? 1'b0 : 1'bz;
  assign led = ~c[28:23];
endmodule
