; RUN: opt < %s -passes=instcombine -S | not grep rem

; ---- from apint-rem1.ll ----
; This test makes sure that these instructions are properly eliminated.
; This test is for Integer BitWidth < 64 && BitWidth % 2 != 0.
;


define i33 @test1_g66m0(i33 %A) {
    %B = urem i33 %A, 4096
    ret i33 %B
}

define i49 @test2_g66m0(i49 %A) {
    %B = shl i49 4096, 11
    %Y = urem i49 %A, %B
    ret i49 %Y
}

define i59 @test3_g66m0(i59 %X, i1 %C) {
	%V = select i1 %C, i59 70368744177664, i59 4096
	%R = urem i59 %X, %V
	ret i59 %R
}

; ---- from apint-rem2.ll ----
; This test makes sure that these instructions are properly eliminated.
; This test is for Integer BitWidth >= 64 && BitWidth <= 1024.
;


define i333 @test1_g66m1(i333 %A) {
    %B = urem i333 %A, 70368744177664
    ret i333 %B
}

define i499 @test2_g66m1(i499 %A) {
    %B = shl i499 4096, 111
    %Y = urem i499 %A, %B
    ret i499 %Y
}

define i599 @test3_g66m1(i599 %X, i1 %C) {
	%V = select i1 %C, i599 70368744177664, i599 4096
	%R = urem i599 %X, %V
	ret i599 %R
}
