; RUN: llc < %s -O3 -mtriple=x86_64-- |FileCheck %s

; ---- from constant-hoisting-and.ll ----
define i64 @foo_g135m0(i1 %z, i64 %data1, i64 %data2)
{
; If constant 4294967294 is hoisted to a variable, then we won't be able to use
; the implicit zero extension of 32-bit operations to handle the AND.
entry:
  %val1 = and i64 %data1, 4294967294
  br i1 %z, label %End, label %L_val2

; CHECK: andl    $-2, {{.*}}
; CHECK: andl    $-2, {{.*}}
L_val2:
  %val2 = and i64 %data2, 4294967294
  br label %End

End:
  %p1 = phi i64 [%val1,%entry], [%val2,%L_val2]
  ret i64 %p1
}

; ---- from constant-hoisting-shift-immediate.ll ----
define i64 @foo_g135m1(i1 %z, ptr %p, ptr %q)
{
; If const 128 is hoisted to a variable, then in basic block L_val2 we would
; have %lshr2 = lshr i192 %data2, %const, and the definition of %const would
; be in another basic block. As a result, a very inefficient code might be
; produced. Here we check that this doesn't occur.
entry:
  %data1 = load i192, ptr %p, align 8
  %lshr1 = lshr i192 %data1, 128
  %val1  = trunc i192 %lshr1 to i64
  br i1 %z, label %End, label %L_val2

; CHECK: movq    16(%rdx), %rax
; CHECK-NEXT: retq
L_val2:
  %data2 = load i192, ptr %q, align 8
  %lshr2 = lshr i192 %data2, 128
  %val2  = trunc i192 %lshr2 to i64
  br label %End

End:
  %p1 = phi i64 [%val1,%entry], [%val2,%L_val2]
  ret i64 %p1
}
