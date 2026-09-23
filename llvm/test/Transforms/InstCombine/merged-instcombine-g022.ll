; RUN: opt < %s -passes=instcombine -S

; ---- from 2012-12-14-simp-vgep.ll ----
target datalayout = "e-p:32:32:32-i1:8:8-i8:8:8-i16:16:16-i32:32:32-i64:32:64-f32:32:32-f64:32:64-v64:64:64-v128:128:128-a0:0:64-f80:128:128"

define <4 x i32> @foo_g22m0(ptr %in) {
  %t17 = load <4 x ptr>, ptr %in, align 8
  %t18 = icmp eq <4 x ptr> %t17, zeroinitializer
  %t19 = zext <4 x i1> %t18 to <4 x i32>
  ret <4 x i32> %t19
}

; ---- from vector-type.ll ----
; The code in InstCombiner::FoldSelectOpOp was calling
; Type::getVectorNumElements without checking first if the type was a vector.


define i32 @vselect1_g22m1(i32 %a.coerce, i32 %b.coerce, i32 %c.coerce) {
entry:
  %0 = bitcast i32 %a.coerce to <2 x i16>
  %1 = bitcast i32 %b.coerce to <2 x i16>
  %2 = bitcast i32 %c.coerce to <2 x i16>
  %cmp = icmp sge <2 x i16> %2, zeroinitializer
  %or = select <2 x i1> %cmp, <2 x i16> %0, <2 x i16> %1
  %3 = bitcast <2 x i16> %or to i32
  ret i32 %3
}
