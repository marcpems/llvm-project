; ModuleID = 'leaf'
source_filename = "leaf.c"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-windows-msvc19.33.0"

$__llvm_profile_runtime_user = comdat any

@__llvm_profile_runtime = external hidden global i32
@__profc_leaf = private global [2 x i64] zeroinitializer, section ".lprfc$M", align 8
@__profd_leaf = private global { i64, i64, i64, i64, i64, ptr, ptr, i32, [3 x i16], i16, i32 } { i64 7399155579282764986, i64 99167, i64 sub (i64 ptrtoint (ptr @__profc_leaf to i64), i64 ptrtoint (ptr @__profd_leaf to i64)), i64 0, i64 0, ptr null, ptr null, i32 2, [3 x i16] zeroinitializer, i16 0, i32 0 }, section ".lprfd$0", align 8
@__ImageBase = external dso_local constant i8
@__profd_leaf.rva = private constant i32 trunc (i64 sub (i64 ptrtoint (ptr @__profd_leaf to i64), i64 ptrtoint (ptr @__ImageBase to i64)) to i32), section ".lprfr$M", align 4
@__llvm_prf_nm = private constant [14 x i8] c"\04\0Cx\DA\CBIML\03\00\04\0B\01\99", section ".lprfn$M", align 1
@llvm.compiler.used = appending global [3 x ptr] [ptr @__llvm_profile_runtime_user, ptr @__profd_leaf, ptr @__profd_leaf.rva], section "llvm.metadata"
@__llvm_profile_record_rvas_v2 = external constant i32
@llvm.used = appending global [2 x ptr] [ptr @__llvm_prf_nm, ptr @__llvm_profile_record_rvas_v2], section "llvm.metadata"

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @leaf(i32 noundef %0) #0 {
  %2 = alloca i32, align 4
  store i32 %0, ptr %2, align 4
  %pgocount = load i64, ptr @__profc_leaf, align 8
  %3 = add i64 %pgocount, 1
  store i64 %3, ptr @__profc_leaf, align 8
  %4 = load i32, ptr %2, align 4
  %5 = icmp eq i32 %4, 1
  br i1 %5, label %6, label %8

6:                                                ; preds = %1
  %pgocount1 = load i64, ptr getelementptr inbounds (i8, ptr @__profc_leaf, i64 8), align 8
  %7 = add i64 %pgocount1, 1
  store i64 %7, ptr getelementptr inbounds (i8, ptr @__profc_leaf, i64 8), align 8
  br label %10

8:                                                ; preds = %1
  %9 = load i32, ptr %2, align 4
  br label %10

10:                                               ; preds = %8, %6
  %11 = phi i32 [ 3, %6 ], [ %9, %8 ]
  ret i32 %11
}

; Function Attrs: nounwind
declare void @llvm.instrprof.increment(ptr, i64, i32, i32) #1

; Function Attrs: noinline
define linkonce_odr hidden i32 @__llvm_profile_runtime_user() #2 comdat !prof !11 {
  %1 = load i32, ptr @__llvm_profile_runtime, align 4
  ret i32 %1
}

attributes #0 = { noinline nounwind uwtable "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nounwind }
attributes #2 = { noinline }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5, !6}
!llvm.linker.options = !{!7, !8, !9}
!llvm.ident = !{!10}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "clang version 23.1.4 (https://github.com/llvm/llvm-project 7a941dfb2877a0b8cf30323fefa85ad019e0b0f5)", isOptimized: true, runtimeVersion: 0, emissionKind: NoDebug, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "leaf.c", directory: ".")
!2 = !{i32 2, !"EnableValueProfiling", i32 0}
!3 = !{i32 2, !"Debug Info Version", i32 3}
!4 = !{i32 8, !"PIC Level", i32 2}
!5 = !{i32 7, !"uwtable", i32 2}
!6 = !{i32 1, !"MaxTLSAlign", i32 65536}
!7 = !{!"/DEFAULTLIB:clang_rt.profile.lib"}
!8 = !{!"/DEFAULTLIB:libcmt.lib"}
!9 = !{!"/DEFAULTLIB:oldnames.lib"}
!10 = !{!"clang version 23.1.4 (https://github.com/llvm/llvm-project 7a941dfb2877a0b8cf30323fefa85ad019e0b0f5)"}
!11 = !{!"function_entry_count", i64 0}
