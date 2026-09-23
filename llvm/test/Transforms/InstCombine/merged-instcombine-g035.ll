; RUN: opt < %s -passes=instcombine -S | grep "ret i1 false"

; ---- from 2008-10-11-DivCompareFold.ll ----
; PR2697

define i1 @x_g35m0(i32 %x_g35m0) nounwind {
	%div = sdiv i32 %x_g35m0, 65536		; <i32> [#uses=1]
	%cmp = icmp slt i32 %div, -65536
	ret i1 %cmp
}

; ---- from srem-simplify-bug.ll ----
; PR2276

define i1 @f_g35m1(i32 %x) {
  %A = or i32 %x, 1
  %B = srem i32 %A, 1
  %C = icmp ne i32 %B, 0
  ret i1 %C
}
