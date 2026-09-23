; RUN: llc < %s -mtriple=x86_64-- -mcpu=corei7

; ---- from 2012-07-16-LeaUndef.ll ----
define void @autogen_SD2543_g284m0() {
A:
  %E83 = add i32 0, 1
  %E820 = add i32 0, undef
  br label %C
C:
  %B908 = add i32 %E83, %E820
  store i32 %B908, ptr undef
  %Sl2391 = select i1 undef, i32 undef, i32 %E83
  %Cmp3114 = icmp ne i32 %Sl2391, undef
  br i1 %Cmp3114, label %C, label %G
G:
  ret void
}

; ---- from 2012-07-16-fp2ui-i1.ll ----
define void @autogen_SD3100_g284m1() {
BB:
  %FC123 = fptoui float 0x40693F5D00000000 to i1
  br i1 %FC123, label %V, label %W

V:
  ret void
W:
  ret void
}

; ---- from 2012-07-17-vtrunc.ll ----
define void @autogen_SD33189483_g284m2() {
BB:
  br label %CF76

CF76:                                             ; preds = %CF76, %BB
  %Shuff13 = shufflevector <4 x i64> zeroinitializer, <4 x i64> undef, <4 x i32> zeroinitializer
  %Tr16 = trunc <8 x i64> <i64 -1, i64 -1, i64 -1, i64 -1, i64 -1, i64 -1, i64 -1, i64 -1> to <8 x i1>
  %E19 = extractelement <8 x i1> %Tr16, i32 2
  br i1 %E19, label %CF76, label %CF78

CF78:                                             ; preds = %CF78, %CF76
  %BC = bitcast <4 x i64> %Shuff13 to <4 x double>
  br label %CF78
}
