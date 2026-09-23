; RUN: llc < %s -mtriple=i686-- -mattr=-sse2,-sse3 | FileCheck %s

; ---- from fp-immediate-shorten.ll ----
;; Test that this FP immediate is stored in the constant pool as a float.


; CHECK: {{.long.0x42f60000}}

define double @D_g204m0() {
        ret double 1.230000e+02
}

; ---- from negative_zero.ll ----
; CHECK: fchs


define double @T_g204m1() {
	ret double -1.0   ;; codegen as fld1/fchs, not as a load from cst pool
}
