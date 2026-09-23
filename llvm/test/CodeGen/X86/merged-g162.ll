; RUN: llc < %s -mtriple=i386-apple-darwin

; ---- from 2008-09-19-RegAllocBug.ll ----
; PR2808

@g_3 = external global i32		; <ptr> [#uses=1]

define i32 @func_4_g162m0() nounwind {
entry:
	%0 = load i32, ptr @g_3, align 4		; <i32> [#uses=2]
	%1 = trunc i32 %0 to i8		; <i8> [#uses=1]
	%2 = sub i8 1, %1		; <i8> [#uses=1]
	%3 = sext i8 %2 to i32		; <i32> [#uses=1]
	%cmp2 = icmp ugt i32 ptrtoint (ptr @func_4_g162m0 to i32), 3
	%ext = zext i1 %cmp2 to i8
	%c = icmp ne i8 %ext, 0
	%s = select i1 %c, i32 0, i32 ptrtoint (ptr @func_4_g162m0 to i32)
	%ashr = ashr i32 %3, %s
	%urem = urem i32 %0, %ashr
	%cmp = icmp eq i32 %urem, 0
	br i1 %cmp, label %return, label %bb4

bb4:		; preds = %entry
	ret i32 undef

return:		; preds = %entry
	ret i32 undef
}

; ---- from 2009-10-14-LiveVariablesBug.ll ----
; rdar://7299435

@i_g162m1 = internal global i32 0                        ; <ptr> [#uses=1]
@llvm.used_g162m1 = appending global [1 x ptr] [ptr @foo_g162m1], section "llvm.metadata" ; <ptr> [#uses=0]

define void @foo_g162m1(i16 signext %source) nounwind ssp {
entry:
  %source_addr = alloca i16, align 2              ; <ptr> [#uses=2]
  store i16 %source, ptr %source_addr
  store i32 4, ptr @i_g162m1, align 4
  call void asm sideeffect "# top of block", "~{dirflag},~{fpsr},~{flags},~{edi},~{esi},~{edx},~{ecx},~{eax}"() nounwind
  %asmtmp = call i16 asm sideeffect "movw $1, $0", "=={ax},*m,~{dirflag},~{fpsr},~{flags},~{memory}"(ptr elementtype(i16) %source_addr) nounwind ; <i16> [#uses=0]
  ret void
}
