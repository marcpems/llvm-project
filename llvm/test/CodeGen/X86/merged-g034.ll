; RUN: llc -mtriple x86_64-pc-linux-gnu < %s | FileCheck %s

; ---- from elf-comdat.ll ----
$f_g34m0 = comdat any
@v_g34m0 = global i32 0, comdat($f_g34m0)
define void @f_g34m0() comdat($f_g34m0) {
  ret void
}
; CHECK: .section        .text.f_g34m0,"axG",@progbits,f_g34m0,comdat
; CHECK: .globl  f_g34m0
; CHECK: .section        .bss.v_g34m0,"awG",@nobits,f_g34m0,comdat
; CHECK: .globl  v_g34m0

; ---- from elf-comdat2.ll ----
$foo_g34m1 = comdat any
@bar_g34m1 = global i32 42, comdat($foo_g34m1)
@foo_g34m1 = global i32 42

; CHECK:      .type   bar_g34m1,@object
; CHECK-NEXT: .section        .data.bar_g34m1,"awG",@progbits,foo_g34m1,comdat
; CHECK-NEXT: .globl  bar_g34m1
; CHECK:      .type   foo_g34m1,@object
; CHECK-NEXT: .data
; CHECK-NEXT: .globl  foo_g34m1
