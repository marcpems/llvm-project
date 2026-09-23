; RUN: llc < %s -mtriple=i686-unknown-linux -tailcallopt | FileCheck %s

; ---- from tailcall-structret.ll ----
define fastcc { ptr, ptr} @init_g241m0({ ptr, ptr}, i32) {
entry:
      %2 = tail call fastcc { ptr, ptr } @init_g241m0({ ptr, ptr} %0, i32 %1)
      ret { ptr, ptr} %2
; CHECK: jmp init_g241m0
}

; ---- from tailcallbyval.ll ----
%struct.s = type {i32, i32, i32, i32, i32, i32, i32, i32,
                  i32, i32, i32, i32, i32, i32, i32, i32,
                  i32, i32, i32, i32, i32, i32, i32, i32 }

define  fastcc i32 @tailcallee_g241m1(ptr byval(%struct.s) %a) nounwind {
entry:
        %tmp3 = load i32, ptr %a
        ret i32 %tmp3
; CHECK: tailcallee_g241m1
; CHECK: movl 4(%esp), %eax
}

define  fastcc i32 @tailcaller_g241m1(ptr byval(%struct.s) %a) nounwind {
entry:
        %tmp4 = tail call fastcc i32 @tailcallee_g241m1(ptr byval(%struct.s) %a )
        ret i32 %tmp4
; CHECK: tailcaller_g241m1
; CHECK: jmp tailcallee_g241m1
}
