; RUN: opt < %s -passes=instcombine -S | grep "ret i1 true"

; ---- from 2007-06-21-DivCompareMiscomp.ll ----
; rdar://5278853

define i1 @test_g37m0(i32 %tmp468) {
        %tmp470 = udiv i32 %tmp468, 4           ; <i32> [#uses=2]
        %tmp475 = icmp ult i32 %tmp470, 1073741824              ; <i1> [#uses=1]
        ret i1 %tmp475
}

; ---- from 2008-11-01-SRemDemandedBits.ll ----
; PR2993

define i1 @foo_g37m1(i32 %x) {
  %1 = srem i32 %x, -1
  %2 = icmp eq i32 %1, 0
  ret i1 %2
}
