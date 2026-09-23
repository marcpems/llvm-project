; RUN: llc < %s -mtriple=i686--

; ---- from 2003-08-23-DeadBlockTest.ll ----
define i32 @test_g186m0() {
entry:
        ret i32 7
Test:           ; No predecessors!
        %A = call i32 @test_g186m0( )          ; <i32> [#uses=1]
        %B = call i32 @test_g186m0( )          ; <i32> [#uses=1]
        %C = add i32 %A, %B             ; <i32> [#uses=1]
        ret i32 %C
}

; ---- from 2004-02-22-Casts.ll ----
define i1 @test1_g186m1(double %X) {
        %V = fcmp one double %X, 0.000000e+00           ; <i1> [#uses=1]
        ret i1 %V
}

define double @test2_g186m1(i64 %X) {
        %V = uitofp i64 %X to double            ; <double> [#uses=1]
        ret double %V
}

; ---- from 2004-04-13-FPCMOV-Crash.ll ----
define double @test_g186m2(double %d) {
        %X = select i1 false, double %d, double %d              ; <double> [#uses=1]
        ret double %X
}

; ---- from 2004-06-10-StackifierCrash.ll ----
define i1 @T_g186m3(double %X) {
        %V = fcmp oeq double %X, %X             ; <i1> [#uses=1]
        ret i1 %V
}

; ---- from 2004-10-08-SelectSetCCFold.ll ----
define i1 @test_g186m4(i1 %C, i1 %D, i32 %X, i32 %Y) {
        %E = icmp slt i32 %X, %Y                ; <i1> [#uses=1]
        %F = select i1 %C, i1 %D, i1 %E         ; <i1> [#uses=1]
        ret i1 %F
}

; ---- from 2006-07-10-InlineAsmAConstraint.ll ----
; PR825

define i64 @test_g186m5() {
	%tmp.i5 = call i64 asm sideeffect "rdtsc", "=A,~{dirflag},~{fpsr},~{flags}"( )		; <i64> [#uses=1]
	ret i64 %tmp.i5
}

; ---- from 2006-10-09-CycleInDAG.ll ----
define void @_ZN13QFSFileEngine4readEPcx_g186m6() {
	%tmp201 = load i32, ptr null		; <i32> [#uses=1]
	%tmp201.upgrd.1 = sext i32 %tmp201 to i64		; <i64> [#uses=1]
	%tmp202 = load i64, ptr null		; <i64> [#uses=1]
	%tmp203 = add i64 %tmp201.upgrd.1, %tmp202		; <i64> [#uses=1]
	store i64 %tmp203, ptr null
	ret void
}

; ---- from 2006-10-13-CycleInDAG.ll ----
@str = external dso_local global [18 x i8]		; <ptr> [#uses=1]

define void @test_g186m7() {
bb.i:
	%tmp.i660 = load <4 x float>, ptr null		; <<4 x float>> [#uses=1]
	call void (i32, ...) @printf( i32 0, ptr @str, double 0.000000e+00, double 0.000000e+00, double 0.000000e+00, double 0.000000e+00 )
	%tmp152.i = load <4 x i32>, ptr null		; <<4 x i32>> [#uses=1]
	%tmp156.i = bitcast <4 x i32> %tmp152.i to <4 x i32>		; <<4 x i32>> [#uses=1]
	%tmp175.i = bitcast <4 x float> %tmp.i660 to <4 x i32>		; <<4 x i32>> [#uses=1]
	%tmp176.i = xor <4 x i32> %tmp156.i, < i32 -1, i32 -1, i32 -1, i32 -1 >		; <<4 x i32>> [#uses=1]
	%tmp177.i = and <4 x i32> %tmp176.i, %tmp175.i		; <<4 x i32>> [#uses=1]
	%tmp190.i = or <4 x i32> %tmp177.i, zeroinitializer		; <<4 x i32>> [#uses=1]
	%tmp191.i = bitcast <4 x i32> %tmp190.i to <4 x float>		; <<4 x float>> [#uses=1]
	store <4 x float> %tmp191.i, ptr null
	ret void
}

declare void @printf(i32, ...)

; ---- from 2007-01-29-InlineAsm-ir.ll ----
; Test 'ri' constraint.

define void @run_init_process_g186m8() {
          %tmp = call i32 asm sideeffect "push %ebx ; movl $2,%ebx ; int $$0x80 ; pop %ebx", "={ax},0,ri,{cx},{dx},~{dirflag},~{fpsr},~{flags},~{memory}"( i32 11, i32 0, i32 0, i32 0 )          
          unreachable
  }

; ---- from 2007-03-16-InlineAsm.ll ----
; ModuleID = 'a.bc'

define i32 @foo_g186m9(i32 %A, i32 %B) {
entry:
	%A_addr = alloca i32		; <ptr> [#uses=2]
	%B_addr = alloca i32		; <ptr> [#uses=1]
	%retval = alloca i32, align 4		; <ptr> [#uses=2]
	%tmp = alloca i32, align 4		; <ptr> [#uses=2]
	%ret = alloca i32, align 4		; <ptr> [#uses=2]
	store i32 %A, ptr %A_addr
	store i32 %B, ptr %B_addr
	%tmp1 = load i32, ptr %A_addr		; <i32> [#uses=1]
	%tmp2 = call i32 asm "roll $1,$0", "=r,I,0,~{dirflag},~{fpsr},~{flags},~{cc}"( i32 7, i32 %tmp1 )		; <i32> [#uses=1]
	store i32 %tmp2, ptr %ret
	%tmp3 = load i32, ptr %ret		; <i32> [#uses=1]
	store i32 %tmp3, ptr %tmp
	%tmp4 = load i32, ptr %tmp		; <i32> [#uses=1]
	store i32 %tmp4, ptr %retval
	br label %return

return:		; preds = %entry
	%retval5 = load i32, ptr %retval		; <i32> [#uses=1]
	ret i32 %retval5
}

; ---- from 2007-03-18-LiveIntervalAssert.ll ----
; PR1259

define void @test_g186m10() {
        %tmp2 = call i32 asm "...", "=r,~{dirflag},~{fpsr},~{flags},~{dx},~{cx},~{ax}"( )
        unreachable
}

; ---- from 2007-03-24-InlineAsmMultiRegConstraint.ll ----
define i32 @test_g186m11(i16 %tmp40414244) {
  %tmp48 = call i32 asm sideeffect "inl ${1:w}, $0", "={ax},N{dx},~{dirflag},~{fpsr},~{flags}"( i16 %tmp40414244 )
  ret i32 %tmp48
}

define i32 @test2_g186m11(i16 %tmp40414244) {
  %tmp48 = call i32 asm sideeffect "inl ${1:w}, $0", "={ax},N{dx},~{dirflag},~{fpsr},~{flags}"( i16 14 )
  ret i32 %tmp48
}

; ---- from 2008-02-05-ISelCrash.ll ----
; PR1975

@nodes = external dso_local global i64		; <ptr> [#uses=2]

define fastcc i32 @ab_g186m12(i32 %alpha, i32 %beta) nounwind  {
entry:
	%tmp1 = load i64, ptr @nodes, align 8		; <i64> [#uses=1]
	%tmp2 = add i64 %tmp1, 1		; <i64> [#uses=1]
	store i64 %tmp2, ptr @nodes, align 8
	ret i32 0
}

; ---- from 2008-03-19-DAGCombinerBug.ll ----
define i32 @t_g186m13() nounwind  {
entry:
	%tmp54 = add i32 0, 1		; <i32> [#uses=1]
	br i1 false, label %bb71, label %bb77
bb71:		; preds = %entry
	%tmp74 = shl i32 %tmp54, 1		; <i32> [#uses=1]
	%tmp76 = ashr i32 %tmp74, 3		; <i32> [#uses=1]
	br label %bb77
bb77:		; preds = %bb71, %entry
	%payLoadSize.0 = phi i32 [ %tmp76, %bb71 ], [ 0, %entry ]		; <i32> [#uses=0]
	unreachable
}

; ---- from 2008-04-28-CyclicSchedUnit.ll ----
define i64 @t_g186m14(i64 %maxIdleDuration) nounwind  {
	call void asm sideeffect "wrmsr", "{cx},A,~{dirflag},~{fpsr},~{flags}"( i32 416, i64 0 ) nounwind 
	unreachable
}

; ---- from 2008-05-09-PHIElimBug.ll ----
%struct.V = type { <4 x float>, <4 x float>, <4 x float>, <4 x float>, <4 x float>, <4 x float>, <4 x float>, <4 x i32>, ptr, ptr, ptr, ptr, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, i32, i32, i32, i32, i32, i32, i32, i32 }

define fastcc void @t_g186m15() nounwind  {
entry:
	br i1 false, label %bb23816.preheader, label %bb23821

bb23816.preheader:		; preds = %entry
	%tmp23735 = and i32 0, 2		; <i32> [#uses=0]
	br label %bb23830

bb23821:		; preds = %entry
	br i1 false, label %bb23830, label %bb23827

bb23827:		; preds = %bb23821
	%tmp23829 = getelementptr %struct.V, ptr null, i32 0, i32 42		; <ptr> [#uses=0]
	br label %bb23830

bb23830:		; preds = %bb23827, %bb23821, %bb23816.preheader
	%scaledInDst.2.reg2mem.5 = phi i8 [ undef, %bb23827 ], [ undef, %bb23821 ], [ undef, %bb23816.preheader ]		; <i8> [#uses=1]
	%toBool35047 = icmp eq i8 %scaledInDst.2.reg2mem.5, 0		; <i1> [#uses=1]
	%bothcond39107 = or i1 %toBool35047, false		; <i1> [#uses=0]
	unreachable
}

; ---- from 2008-10-29-ExpandVAARG.ll ----
; PR2977
define ptr @ap_php_conv_p2_g186m16(){
entry:
        %ap.addr = alloca ptr           ; <ptr> [#uses=36]
        br label %sw.bb301
sw.bb301:
        %0 = va_arg ptr %ap.addr, i64          ; <i64> [#uses=1]
        br label %sw.bb301
}

; ---- from 2009-02-08-CoalescerBug.ll ----
; PR3486

define i32 @foo_g186m17(i8 signext %p_26) nounwind {
entry:
	%0 = icmp eq i8 %p_26, 0		; <i1> [#uses=2]
	%or.cond = or i1 false, %0		; <i1> [#uses=2]
	%iftmp.1.0 = zext i1 %or.cond to i16		; <i16> [#uses=1]
	br i1 %0, label %bb.i, label %bar.exit

bb.i:		; preds = %entry
	%1 = zext i1 %or.cond to i32		; <i32> [#uses=1]
	%2 = sdiv i32 %1, 0		; <i32> [#uses=1]
	%3 = trunc i32 %2 to i16		; <i16> [#uses=1]
	br label %bar.exit

bar.exit:		; preds = %bb.i, %entry
	%4 = phi i16 [ %3, %bb.i ], [ %iftmp.1.0, %entry ]		; <i16> [#uses=1]
	%5 = trunc i16 %4 to i8		; <i8> [#uses=1]
	%6 = sext i8 %5 to i32		; <i32> [#uses=1]
	ret i32 %6
}

; ---- from 2009-03-03-BitcastLongDouble.ll ----
; PR3686
; rdar://6661799

define i32 @x_g186m18(i32 %y) nounwind readnone {
entry:
	%tmp14 = zext i32 %y to i80		; <i80> [#uses=1]
	%tmp15 = bitcast i80 %tmp14 to x86_fp80		; <x86_fp80> [#uses=1]
	%add = fadd x86_fp80 %tmp15, 0xK3FFF8000000000000000		; <x86_fp80> [#uses=1]
	%tmp11 = bitcast x86_fp80 %add to i80		; <i80> [#uses=1]
	%tmp10 = trunc i80 %tmp11 to i32		; <i32> [#uses=1]
	ret i32 %tmp10
}

; ---- from 2009-07-07-SplitICmp.ll ----
define void @test2_g186m19(<2 x i32> %A, <2 x i32> %B, ptr %C) nounwind {
       %D = icmp sgt <2 x i32> %A, %B
       %E = zext <2 x i1> %D to <2 x i32>
       store <2 x i32> %E, ptr %C
       ret void
}

; ---- from 2009-07-09-ExtractBoolFromVector.ll ----
; PR3037

define void @entry_g186m20(ptr %dest) {
	%1 = xor <4 x i1> zeroinitializer, < i1 true, i1 true, i1 true, i1 true >
	%2 = extractelement <4 x i1> %1, i32 3
	%3 = zext i1 %2 to i8
	%4 = insertelement <4 x i8> zeroinitializer, i8 %3, i32 3
	store <4 x i8> %4, ptr %dest, align 1
	ret void
}

; ---- from 2009-07-20-DAGCombineBug.ll ----
@bsBuff_g186m21 = internal global i32 0		; <ptr> [#uses=1]
@llvm.used_g186m21 = appending global [1 x ptr] [ptr @bsGetUInt32_g186m21], section "llvm.metadata"		; <ptr> [#uses=0]

define fastcc i32 @bsGetUInt32_g186m21() nounwind ssp {
entry:
	%bsBuff_g186m21.promoted44 = load i32, ptr @bsBuff_g186m21		; <i32> [#uses=1]
	%0 = add i32 0, -8		; <i32> [#uses=1]
	%1 = lshr i32 %bsBuff_g186m21.promoted44, %0		; <i32> [#uses=1]
	%2 = shl i32 %1, 8		; <i32> [#uses=1]
	br label %bb3.i17

bb3.i9:		; preds = %bb3.i17
	br i1 false, label %bb2.i16, label %bb1.i15

bb1.i15:		; preds = %bb3.i9
	unreachable

bb2.i16:		; preds = %bb3.i9
	br label %bb3.i17

bb3.i17:		; preds = %bb2.i16, %entry
	br i1 false, label %bb3.i9, label %bsR.exit18

bsR.exit18:		; preds = %bb3.i17
	%3 = or i32 0, %2		; <i32> [#uses=0]
	ret i32 0
}

; ---- from 2011-03-30-CreateFixedObjCrash.ll ----
; rdar://7983260

%struct.T0 = type {}

define void @fn4_g186m22(ptr byval(%struct.T0) %arg0) nounwind ssp {
entry:
  ret void
}

; ---- from i2k.ll ----
define void @foo_g186m23(ptr %x, ptr %y, ptr %p) nounwind {
  %a = load i2011, ptr %x
  %b = load i2011, ptr %y
  %c = add i2011 %a, %b
  store i2011 %c, ptr %p
  ret void
}

; ---- from negative-subscript.ll ----
; rdar://6559995

@a = external dso_local global [255 x ptr], align 32

define i32 @main_g186m24() nounwind {
entry:
	store ptr getelementptr ([255 x ptr], ptr @a, i32 0, i32 -2147483624), ptr getelementptr ([255 x ptr], ptr @a, i32 0, i32 16), align 32
	ret i32 0
}

; ---- from pr10068.ll ----
define void @foobar_g186m25() {
entry:
  %sub.i = trunc i64 undef to i32
  %shr80.i = ashr i32 %sub.i, 16
  %add82.i = add nsw i32 %shr80.i, 1
  %notlhs.i = icmp slt i32 %shr80.i, undef
  %notrhs.i = icmp sgt i32 %add82.i, -1
  %or.cond.not.i = and i1 %notrhs.i, %notlhs.i
  %cmp154.i = icmp slt i32 0, undef
  %or.cond406.i = and i1 %or.cond.not.i, %cmp154.i
  %or.cond406.not.i = xor i1 %or.cond406.i, true
  %or.cond407.i = or i1 undef, %or.cond406.not.i
  br i1 %or.cond407.i, label %if.then158.i, label %if.end163.i

if.then158.i:
  ret void

if.end163.i:                                      ; preds = %if.end67.i
  ret void
}

; ---- from pr26652.ll ----
; PR26652

define <2 x i32> @test_g186m26(<4 x i32> %a, <4 x i32> %b) {
entry:
  %0 = or <4 x i32> %a, %b
  %1 = shufflevector <4 x i32> %0, <4 x i32> undef, <2 x i32> <i32 2, i32 3>
  ret <2 x i32> %1
}

; ---- from weak.ll ----
@a_g186m27 = extern_weak global i32             ; <ptr> [#uses=1]
@b_g186m27 = global ptr @a_g186m27             ; <ptr> [#uses=0]
