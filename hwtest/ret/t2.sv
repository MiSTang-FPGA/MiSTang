module t2(input clk, input s1, input s2, inout recon, output flash_cs_n, flash_clk, flash_mosi, output [5:0] led);
wire arm; reg [26:0] c=0; always @(posedge clk) c<=c+1;
mistang_return r(.clk(clk),.btn_a(1'b1),.btn_b(1'b1),.fl_cs_n_i(1'b1),.fl_clk_i(1'b0),.fl_mosi_i(1'b0),.flash_cs_n(flash_cs_n),.flash_clk(flash_clk),.flash_mosi(flash_mosi),.reconfig_n(recon),.armed(arm));
assign led = ~{c[26:22]|{5{arm}}, 1'b0};
endmodule
