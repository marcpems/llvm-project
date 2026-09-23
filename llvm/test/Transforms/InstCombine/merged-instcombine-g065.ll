; RUN: opt < %s -passes=instcombine -S | not grep mul

; ---- from 2008-02-23-MulSub.ll ----
define i26 @test_g65m0(i26 %a) nounwind  {
entry:
	%_add = mul i26 %a, 2885		; <i26> [#uses=1]
	%_shl2 = mul i26 %a, 2884		; <i26> [#uses=1]
	%_sub = sub i26 %_add, %_shl2		; <i26> [#uses=1]
	ret i26 %_sub
}

; ---- from 2008-11-27-MultiplyIntVec.ll ----
define <2 x i8> @f_g65m1(<2 x i8> %x) {
  %A = mul <2 x i8> %x, <i8 1, i8 1>
  ret <2 x i8> %A
}

define <2 x i8> @g_g65m1(<2 x i8> %x) {
  %A = mul <2 x i8> %x, <i8 -1, i8 -1>
  ret <2 x i8> %A
}
