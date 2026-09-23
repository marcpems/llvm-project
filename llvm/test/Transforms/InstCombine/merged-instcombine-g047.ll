; RUN: opt < %s -passes=instcombine -S | grep and

; ---- from 2006-09-15-CastToBool.ll ----
; PR913

define i32 @test_g47m0(ptr %tmp1) {
        %tmp.i = load i32, ptr %tmp1                ; <i32> [#uses=1]
        %tmp = bitcast i32 %tmp.i to i32                ; <i32> [#uses=1]
        %tmp2.ui = lshr i32 %tmp, 5             ; <i32> [#uses=1]
        %tmp2 = bitcast i32 %tmp2.ui to i32             ; <i32> [#uses=1]
        %tmp3 = and i32 %tmp2, 1                ; <i32> [#uses=1]
        %tmp3.upgrd.1 = icmp ne i32 %tmp3, 0            ; <i1> [#uses=1]
        %tmp34 = zext i1 %tmp3.upgrd.1 to i32           ; <i32> [#uses=1]
        ret i32 %tmp34
}

; ---- from 2007-03-25-DoubleShift.ll ----
; PR1271
define i1 @test_g47m1(i32 %tmp13) {
entry:
	%tmp14 = shl i32 %tmp13, 12		; <i32> [#uses=1]
	%tmp15 = lshr i32 %tmp14, 12		; <i32> [#uses=1]
	%res = icmp ne i32 %tmp15, 0		; <i1>:3 [#uses=1]
        ret i1 %res
}
