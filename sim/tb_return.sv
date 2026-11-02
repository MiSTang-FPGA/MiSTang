`timescale 1ns/1ps
module tb;
reg clk=0, a=0, b=0; always #18.5 clk=~clk;
wire cs, sck, mosi, rc;
reg fcs=1, fck=0, fmo=0;
mistang_return dut(.clk(clk),.btn_a(a),.btn_b(b),.fl_cs_n_i(fcs),.fl_clk_i(fck),.fl_mosi_i(fmo),.flash_cs_n(cs),.flash_clk(sck),.flash_mosi(mosi),.reconfig_n(rc),.armed());
reg [7:0] sh=0; integer n=0; reg seen_rc=0; time t_fire=0, t_rc=0;
always @(posedge sck) if (dut.own && cs===1'b0) begin sh <= {sh[6:0], mosi}; n <= n+1; end
always @(negedge rc) begin seen_rc<=1; t_rc=$time; end
initial begin
  #100 a=1; b=1; #2000 dut.c = 22'h1e0000;
  #(200_000); 
  $display("bits=%0d byte=%02x rc_low=%0d cs_during=%b", n, sh, seen_rc, cs);
  if (n==8 && sh==8'hAB && seen_rc) $display("PASS"); else $display("FAIL");
  $finish;
end
endmodule
