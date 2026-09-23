; RUN: llc < %s  -mtriple=i686-pc-linux-gnu -relocation-model=pic | FileCheck %s

; ---- from tailccpic1.ll ----
; This test uses guaranteed TCO so these will be tail calls, despite the early
; binding issues.

define protected tailcc i32 @tailcallee_g126m0(i32 %a1, i32 %a2, i32 %a3, i32 %a4) {
entry:
	ret i32 %a3
}

define tailcc i32 @tailcaller_g126m0(i32 %in1, i32 %in2) {
entry:
	%tmp11 = tail call tailcc i32 @tailcallee_g126m0( i32 %in1, i32 %in2, i32 %in1, i32 %in2 )		; <i32> [#uses=1]
	ret i32 %tmp11
; CHECK: jmp tailcallee_g126m0
}

; ---- from tailccpic2.ll ----
define tailcc i32 @tailcallee_g126m1(i32 %a1, i32 %a2, i32 %a3, i32 %a4) {
entry:
	ret i32 %a3
}

define tailcc i32 @tailcaller_g126m1(i32 %in1, i32 %in2) {
entry:
	%tmp11 = tail call tailcc i32 @tailcallee_g126m1( i32 %in1, i32 %in2, i32 %in1, i32 %in2 )		; <i32> [#uses=1]
	ret i32 %tmp11
; CHECK: movl tailcallee_g126m1@GOT
; CHECK: jmpl
}
