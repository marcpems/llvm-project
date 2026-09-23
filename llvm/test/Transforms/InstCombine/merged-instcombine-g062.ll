; RUN: opt < %s -passes=instcombine -S | not grep bitcast

; ---- from 2007-11-25-CompatibleAttributes.ll ----
; PR1716

@.str = internal constant [4 x i8] c"%d\0A\00"		; <ptr> [#uses=1]

define i32 @main_g62m0(i32 %argc, ptr %argv) {
entry:
	%tmp32 = tail call i32 (ptr  , ...) @printf( ptr @.str  , i32 0 ) nounwind 		; <i32> [#uses=0]
	ret i32 undef
}

declare i32 @printf(ptr, ...) nounwind

; ---- from apint-cast-and-cast.ll ----
define i19 @test1_g62m1(i43 %val) {
  %t1 = bitcast i43 %val to i43 
  %t2 = and i43 %t1, 1
  %t3 = trunc i43 %t2 to i19
  ret i19 %t3
}

define i73 @test2_g62m1(i677 %val) {
  %t1 = bitcast i677 %val to i677 
  %t2 = and i677 %t1, 1
  %t3 = trunc i677 %t2 to i73
  ret i73 %t3
}
