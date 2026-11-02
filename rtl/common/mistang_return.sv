// MiSTang "return to launcher": hold both buttons ~1.2 s and the core
//   1. takes over the SPI flash pins and sends 0xAB (release from deep power-down; cores may have put the flash to sleep),
//   2. releases the pins and pulls RECONFIG_N (pin 9) low: the FPGA reloads the bitstream at the multiboot address in its header.
// Runs on the 27 MHz board clock, independent of PLLs and the soft CPU. Pack WITHOUT --reconfign_as_gpio.
// Written for the Game Boy core, which leaves almost no spare LUTs: the hold timer is an LFSR and the flash
// flash sequence is a tiny constant ROM indexed by a step counter. No flip-flop has a non-zero power-up value.
module mistang_return (
    input  clk,
    input  btn_a, btn_b,                       // raw buttons, active high (async)
    input  fl_cs_n_i, fl_clk_i, fl_mosi_i,     // flash pins as the core drives them
    output flash_cs_n, flash_clk, flash_mosi,
    inout  reconfig_n,
    output armed                               // 1 once the hold completed (debug / LED)
);
localparam [7:0]  CMD_RELEASE_PD = 8'hAB;
localparam [21:0] HOLD_STATE = 22'h1e0000;            // XNOR-LFSR state after 2 000 000 ticks (1.19 s) from zero

// step s = 0..31, one step per 16 clocks (0.6 us): bit 31-s of each pattern
function automatic [31:0] pat(input integer which);
    integer s; reg v;
    begin
        pat = 32'd0;
        for (s = 0; s < 32; s = s + 1) begin
            case (which)
                0: v = (s < 4) || (s >= 22);                                        // CS high outside the command
                1: v = (s >= 5 && s <= 20) && (s % 2 == 0);                         // SCK high on even steps 6..20
                2: v = (s >= 5 && s <= 20) && CMD_RELEASE_PD[7 - ((s - 5) / 2)];    // MOSI
                default: v = 1'b0;
            endcase
            pat[31 - s] = v;
        end
    end
endfunction

reg [1:0]  sa, sb;
reg [3:0]  pre = 0;
reg [21:0] c = 22'd0;
reg        fire = 0;
reg [5:0]  st = 0;                              // steps after fire; bit 5 = done
wire tick = &pre;
always @(posedge clk) begin
    sa <= {sa[0], btn_a}; sb <= {sb[0], btn_b};
    pre <= pre + 1'b1;
    if (tick) begin
        if (!fire) begin
            if (sa[1] & sb[1]) begin c <= {c[20:0], ~(c[21] ^ c[20])}; if (c == HOLD_STATE) fire <= 1'b1; end
            else c <= 22'd0;
        end else if (!st[5]) st <= st + 1'b1;
    end
end
localparam [31:0] P_CS = pat(0), P_CK = pat(1), P_MO = pat(2);
wire [4:0] i = ~st[4:0];                         // bit 31-s
wire own = fire & ~st[5];
wire go  = fire &  st[5];
assign flash_cs_n = own ? P_CS[i] : (fire ? 1'bz : fl_cs_n_i);
assign flash_clk  = own ? P_CK[i] : (fire ? 1'bz : fl_clk_i);
assign flash_mosi = own ? P_MO[i] : (fire ? 1'bz : fl_mosi_i);
assign reconfig_n = go  ? 1'b0 : 1'bz;
assign armed = fire;
endmodule
