; RUN: opt < %s -passes=instcombine -S | not grep div

; ---- from 2008-11-27-IDivVector.ll ----
define <2 x i8> @f_g63m0(<2 x i8> %x) {
  %A = udiv <2 x i8> %x, <i8 1, i8 1>
  ret <2 x i8> %A
}

define <2 x i8> @g_g63m0(<2 x i8> %x) {
  %A = sdiv <2 x i8> %x, <i8 1, i8 1>
  ret <2 x i8> %A
}

; ---- from apint-div1.ll ----
; This test makes sure that div instructions are properly eliminated.
; This test is for Integer BitWidth < 64 && BitWidth % 2 != 0.
;


define i33 @test1_g63m1(i33 %X) {
    %Y = udiv i33 %X, 4096
    ret i33 %Y
}

define i49 @test2_g63m1(i49 %X) {
    %tmp.0 = shl i49 4096, 17
    %Y = udiv i49 %X, %tmp.0
    ret i49 %Y
}

define i59 @test3_g63m1(i59 %X, i1 %C) {
        %V = select i1 %C, i59 1024, i59 4096
        %R = udiv i59 %X, %V
        ret i59 %R
}

; ---- from apint-div2.ll ----
; This test makes sure that div instructions are properly eliminated.
; This test is for Integer BitWidth >= 64 && BitWidth <= 1024.
;


define i333 @test1_g63m2(i333 %X) {
    %Y = udiv i333 %X, 70368744177664
    ret i333 %Y
}

define i499 @test2_g63m2(i499 %X) {
    %tmp.0 = shl i499 4096, 197
    %Y = udiv i499 %X, %tmp.0
    ret i499 %Y
}

define i599 @test3_g63m2(i599 %X, i1 %C) {
        %V = select i1 %C, i599 70368744177664, i599 4096
        %R = udiv i599 %X, %V
        ret i599 %R
}
