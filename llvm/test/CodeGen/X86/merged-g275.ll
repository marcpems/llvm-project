; RUN: llc < %s -mtriple=x86_64-- -mattr=+sse2,+sse4.1

; ---- from pr10523.ll ----
; No check in a crash test

define void @autogen_129334_5000_g275m0() {
BB:
  %I74 = insertelement <32 x i32> undef, i32 undef, i32 15
  %I105 = insertelement <32 x i32> undef, i32 undef, i32 14
  %Shuff292 = shufflevector <32 x i32> %I74, <32 x i32> undef, <32 x i32> <i32 undef, i32 12, i32 14, i32 16, i32 undef, i32 20, i32 22, i32 24, i32 26, i32 28, i32 30, i32 undef, i32 34, i32 36, i32 38, i32 40, i32 42, i32 44, i32 46, i32 48, i32 50, i32 undef, i32 54, i32 undef, i32 undef, i32 undef, i32 undef, i32 0, i32 2, i32 4, i32 6, i32 8>
  %Shuff302 = shufflevector <32 x i32> %Shuff292, <32 x i32> undef, <32 x i32> <i32 27, i32 29, i32 undef, i32 33, i32 undef, i32 37, i32 39, i32 undef, i32 undef, i32 undef, i32 47, i32 undef, i32 51, i32 53, i32 55, i32 57, i32 undef, i32 undef, i32 63, i32 1, i32 undef, i32 undef, i32 undef, i32 9, i32 11, i32 13, i32 undef, i32 17, i32 19, i32 21, i32 23, i32 undef>
  %I326 = insertelement <32 x i32> undef, i32 undef, i32 15
  %B338 = sub <32 x i32> zeroinitializer, %I105
  %FC339 = sitofp <32 x i32> %I326 to <32 x double>
  %S341 = icmp ne <32 x i32> %B338, undef
  %E376 = extractelement <32 x i1> %S341, i32 0
  %Shuff419 = shufflevector <32 x i32> undef, <32 x i32> %Shuff302, <32 x i32> <i32 undef, i32 44, i32 46, i32 48, i32 50, i32 52, i32 undef, i32 56, i32 58, i32 60, i32 62, i32 0, i32 2, i32 4, i32 6, i32 undef, i32 undef, i32 12, i32 14, i32 undef, i32 undef, i32 20, i32 22, i32 undef, i32 26, i32 28, i32 undef, i32 32, i32 34, i32 36, i32 38, i32 40>
  ret void
}

; ---- from pr10524.ll ----
; No check in a crash test

define void @autogen_178513_5000_g275m1() {
BB:
  %Shuff22 = shufflevector <2 x i32> undef, <2 x i32> zeroinitializer, <2 x i32> <i32 3, i32 1>
  %B26 = sub <2 x i32> %Shuff22, zeroinitializer
  %S79 = icmp eq <2 x i32> %B26, zeroinitializer
  %B269 = urem <2 x i1> zeroinitializer, %S79
  %Se335 = sext <2 x i1> %B269 to <2 x i8>
  store <2 x i8> %Se335, ptr undef
  ret void
}

; ---- from pr10525.ll ----
; No check in a crash test

define void @autogen_163411_5000_g275m2() {
BB:
  %L = load <2 x i64>, ptr undef
  %Shuff11 = shufflevector <2 x i64> %L, <2 x i64> %L, <2 x i32> <i32 2, i32 0>
  %I51 = insertelement <2 x i64> undef, i64 undef, i32 0
  %Shuff152 = shufflevector <2 x i64> %I51, <2 x i64> %Shuff11, <2 x i32> <i32 1, i32 3>
  store <2 x i64> %Shuff152, ptr undef
  ret void
}

; ---- from pr10526.ll ----
; No check in a crash test

define void @autogen_142660_5000_g275m3() {
BB:
  %Shuff49 = shufflevector <8 x i32> zeroinitializer, <8 x i32> undef, <8 x i32> <i32 2, i32 4, i32 undef, i32 8, i32 10, i32 12, i32 14, i32 0>
  %B85 = sub <8 x i32> %Shuff49, zeroinitializer
  %S242 = icmp eq <8 x i32> zeroinitializer, %B85
  %FC284 = uitofp <8 x i1> %S242 to <8 x float>
  store <8 x float> %FC284, ptr undef
  ret void
}
