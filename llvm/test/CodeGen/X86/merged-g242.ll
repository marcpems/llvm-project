; RUN: llc < %s -mtriple=i686-unknown-linux | FileCheck %s

; ---- from tailcc-structret.ll ----
define tailcc { ptr, ptr} @init_g242m0({ ptr, ptr}, i32) {
entry:
      %2 = tail call tailcc { ptr, ptr } @init_g242m0({ ptr, ptr} %0, i32 %1)
      ret { ptr, ptr} %2
; CHECK: jmp init_g242m0
}

; ---- from tailccbyval.ll ----
%struct.s = type {i32, i32, i32, i32, i32, i32, i32, i32,
                  i32, i32, i32, i32, i32, i32, i32, i32,
                  i32, i32, i32, i32, i32, i32, i32, i32 }

define  tailcc i32 @tailcallee_g242m1(ptr byval(%struct.s) %a) nounwind {
entry:
        %tmp3 = load i32, ptr %a
        ret i32 %tmp3
; CHECK: tailcallee_g242m1
; CHECK: movl 4(%esp), %eax
}

define  tailcc i32 @tailcaller_g242m1(ptr byval(%struct.s) %a) nounwind {
entry:
        %tmp4 = tail call tailcc i32 @tailcallee_g242m1(ptr byval(%struct.s) %a )
        ret i32 %tmp4
; CHECK: tailcaller_g242m1
; CHECK: jmp tailcallee_g242m1
}
