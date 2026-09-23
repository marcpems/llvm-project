; RUN: llc -mtriple=x86_64-unknown-unknown -no-integrated-as < %s 2>&1 | FileCheck %s

; ---- from inline-asm-n-constraint.ll ----
@x_g108m0 = global i32 0, align 4

define void @foo_g108m0() {
; CHECK-LABEL: foo_g108m0:
  call void asm sideeffect "foo_g108m0 $0", "n"(i32 42) nounwind
; CHECK:      #APP
; CHECK-NEXT: foo_g108m0    $42
; CHECK-NEXT: #NO_APP
  call void asm "# $0", "in"(i32 1392848979)
; CHECK-NEXT: #APP
; CHECK-NEXT: # $1392848979
; CHECK-NEXT: #NO_APP
  ret void
; CHECK-NEXT: retq
}

; ---- from inline-asm-p-constraint.ll ----
define ptr @foo_g108m1(ptr %Ptr) {
; CHECK-LABEL: foo_g108m1:
; asm {mov rax, Pointer; lea rax, Pointer}
; LEA: Computes the effective address of the second operand and stores it in the first operand
  %Ptr.addr = alloca ptr, align 8
  store ptr %Ptr, ptr %Ptr.addr, align 8
; CHECK: movq    %rdi, -8(%rsp)
  %1 = tail call ptr asm "mov ${1:a}, $0\0A\09lea $2, $0", "=r,p,*m,~{dirflag},~{fpsr},~{flags}"(ptr %Ptr, ptr elementtype(ptr) %Ptr.addr)
; CHECK-NEXT: #APP
; CHECK-NEXT: mov (%rdi), %rax
; CHECK-NEXT: lea -8(%rsp), %rax
; CHECK-NEXT: #NO_APP
  ret ptr %1
; CHECK-NEXT: retq
}

define void @intptr_g108m1() {
entry:
; CHECK-LABEL: intptr_g108m1:
; CHECK: ud1l 49150(%eax), %eax
  call void asm "ud1l ${0:a}(%eax), %eax", "p,~{dirflag},~{fpsr},~{flags}"(i32 49150)
  unreachable
}
