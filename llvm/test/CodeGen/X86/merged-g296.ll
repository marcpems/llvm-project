; RUN: llc < %s -mtriple=x86_64-apple-darwin

; ---- from 2007-10-14-CoalescerCrash.ll ----
%struct._Unwind_Context = type {  }

define i32 @execute_stack_op_g296m0(ptr %op_ptr, ptr %op_end, ptr %context, i64 %initial) {
entry:
        br i1 false, label %bb, label %return

bb:             ; preds = %bb31, %entry
        br i1 false, label %bb6, label %bb31

bb6:            ; preds = %bb
        %tmp10 = load i64, ptr null, align 8                ; <i64> [#uses=1]
        %tmp16 = load i64, ptr null, align 8                ; <i64> [#uses=1]
        br i1 false, label %bb23, label %bb31

bb23:           ; preds = %bb6
        %tmp2526.cast = and i64 %tmp16, 4294967295              ; <i64> [#uses=1]
        %tmp27 = ashr i64 %tmp10, %tmp2526.cast         ; <i64> [#uses=1]
        br label %bb31

bb31:           ; preds = %bb23, %bb6, %bb
        %result.0 = phi i64 [ %tmp27, %bb23 ], [ 0, %bb ], [ 0, %bb6 ]          ; <i64> [#uses=0]
        br i1 false, label %bb, label %return

return:         ; preds = %bb31, %entry
        ret i32 undef
}

; ---- from 2009-03-10-CoalescerBug.ll ----
; rdar://r6661945

	%struct.WINDOW = type { i16, i16, i16, i16, i16, i16, i16, i32, i32, i8, i8, i8, i8, i8, i8, i8, i8, i8, i32, ptr, i16, i16, i32, i32, ptr, %struct.pdat, i16, %struct.cchar_t }
	%struct.cchar_t = type { i32, [5 x i32] }
	%struct.ldat = type { ptr, i16, i16, i16 }
	%struct.pdat = type { i16, i16, i16, i16, i16, i16 }

define i32 @pnoutrefresh_g296m1(ptr %win, i32 %pminrow, i32 %pmincol, i32 %sminrow, i32 %smincol, i32 %smaxrow, i32 %smaxcol) nounwind optsize ssp {
entry:
	%0 = load i16, ptr null, align 4		; <i16> [#uses=2]
	%1 = icmp sgt i16 0, %0		; <i1> [#uses=1]
	br i1 %1, label %bb12, label %bb13

bb12:		; preds = %entry
	%2 = sext i16 %0 to i32		; <i32> [#uses=1]
	%3 = sub i32 %2, 0		; <i32> [#uses=1]
	%4 = add i32 %3, %smaxrow		; <i32> [#uses=2]
	%5 = trunc i32 %4 to i16		; <i16> [#uses=1]
	%6 = add i16 0, %5		; <i16> [#uses=1]
	br label %bb13

bb13:		; preds = %bb12, %entry
	%pmaxrow.0 = phi i16 [ %6, %bb12 ], [ 0, %entry ]		; <i16> [#uses=0]
	%smaxrow_addr.0 = phi i32 [ %4, %bb12 ], [ %smaxrow, %entry ]		; <i32> [#uses=1]
	%7 = trunc i32 %smaxrow_addr.0 to i16		; <i16> [#uses=0]
	ret i32 0
}

; ---- from 2010-04-21-CoalescerBug.ll ----
; rdar://7886733

%struct.CMTime = type <{ i64, i32, i32, i64 }>
%struct.CMTimeMapping = type { %struct.CMTimeRange, %struct.CMTimeRange }
%struct.CMTimeRange = type { %struct.CMTime, %struct.CMTime }

define void @t_g296m2(ptr noalias nocapture sret(%struct.CMTimeMapping) %agg.result) nounwind optsize ssp {
entry:
  tail call void @llvm.memcpy.p0.p0.i64(ptr align 4 %agg.result, ptr align 4 null, i64 96, i1 false)
  ret void
}

declare void @llvm.memcpy.p0.p0.i64(ptr nocapture, ptr nocapture, i64, i1) nounwind

; ---- from complex-asm.ll ----
; This formerly crashed.

%0 = type { i64, i64 }

define %0 @f_g296m3() nounwind ssp {
entry:
  %v = alloca %0, align 8
  call void asm sideeffect "", "=*r,r,r,0,~{dirflag},~{fpsr},~{flags}"(ptr elementtype(%0) %v, i32 0, i32 1, i128 undef) nounwind
  %0 = getelementptr inbounds %0, ptr %v, i64 0, i32 0
  %1 = load i64, ptr %0, align 8
  %2 = getelementptr inbounds %0, ptr %v, i64 0, i32 1
  %3 = load i64, ptr %2, align 8
  %mrv4 = insertvalue %0 undef, i64 %1, 0
  %mrv5 = insertvalue %0 %mrv4, i64 %3, 1
  ret %0 %mrv5
}
