; ModuleID = '<stdin>'
source_filename = "instrprof-record-padding.c"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-p:64:64-i32:32-i64:64-i128:128-n32:64-S128-Fn32"
target triple = "aarch64-pc-windows-msvc19.52.37029"

$__llvm_profile_runtime_user = comdat any

@Before = dso_local global [13 x i8] zeroinitializer, section ".lprfd$.", align 8
@After = dso_local global [19 x i8] zeroinitializer, section ".lprfd$1", align 8
@NullRVA = dso_local constant i32 0, section ".lprfr$B", align 4
@Target = dso_local global ptr @callee, align 8
@__llvm_profile_runtime = external hidden global i32
@__profc_callee = private global [2 x i64] zeroinitializer, section ".lprfc$M", align 8
@__profd_callee = private global { i64, i64, i64, i64, i64, ptr, ptr, i32, [3 x i16], i16, i32 } { i64 -6621307527791283157, i64 172590168, i64 sub (i64 ptrtoint (ptr @__profc_callee to i64), i64 ptrtoint (ptr @__profd_callee to i64)), i64 0, i64 0, ptr @callee.local, ptr null, i32 2, [3 x i16] zeroinitializer, i16 0, i32 0 }, section ".lprfd$0", align 8
@__ImageBase = external dso_local constant i8
@__profd_callee.rva = private constant i32 trunc (i64 sub (i64 ptrtoint (ptr @__profd_callee to i64), i64 ptrtoint (ptr @__ImageBase to i64)) to i32), section ".lprfr$M", align 4
@__profc_caller = private global [2 x i64] zeroinitializer, section ".lprfc$M", align 8
@__profvp_caller = private global [1 x i64] zeroinitializer, section ".lprfv$M", align 8
@__profd_caller = private global { i64, i64, i64, i64, i64, ptr, ptr, i32, [3 x i16], i16, i32 } { i64 -1768971689307247648, i64 1180760, i64 sub (i64 ptrtoint (ptr @__profc_caller to i64), i64 ptrtoint (ptr @__profd_caller to i64)), i64 0, i64 0, ptr @caller.local, ptr @__profvp_caller, i32 2, [3 x i16] [i16 1, i16 0, i16 0], i16 0, i32 0 }, section ".lprfd$0", align 8
@__profd_caller.rva = private constant i32 trunc (i64 sub (i64 ptrtoint (ptr @__profd_caller to i64), i64 ptrtoint (ptr @__ImageBase to i64)) to i32), section ".lprfr$M", align 4
@__llvm_prf_vnodes = private global [10 x { i64, i64, ptr }] zeroinitializer, section ".lprfnd$M", align 8
@__llvm_prf_nm = private constant [20 x i8] c"\0D\12x\DAKN\CC\C9IMeL\06QE\00!\9F\04\DB", section ".lprfn$M", align 1
@llvm.compiler.used = appending global [2 x ptr] [ptr @__profd_callee.rva, ptr @__profd_caller.rva], section "llvm.metadata"
@__llvm_profile_record_rvas_v2 = external constant i32
@llvm.used = appending global [9 x ptr] [ptr @Before, ptr @After, ptr @NullRVA, ptr @__llvm_profile_runtime_user, ptr @__profd_callee, ptr @__profd_caller, ptr @__llvm_prf_vnodes, ptr @__llvm_prf_nm, ptr @__llvm_profile_record_rvas_v2], section "llvm.metadata"

@callee.local = private alias i32 (i32), ptr @callee
@caller.local = private alias i32 (), ptr @caller

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @callee(i32 noundef %0) #0 {
  %2 = alloca i32, align 4
  %3 = alloca i32, align 4
  store i32 %0, ptr %3, align 4
  %pgocount = load i64, ptr @__profc_callee, align 8
  %4 = add i64 %pgocount, 1
  store i64 %4, ptr @__profc_callee, align 8
  %5 = load i32, ptr %3, align 4
  %6 = icmp ne i32 %5, 0
  br i1 %6, label %7, label %9

7:                                                ; preds = %1
  %pgocount1 = load i64, ptr getelementptr inbounds (i8, ptr @__profc_callee, i64 8), align 8
  %8 = add i64 %pgocount1, 1
  store i64 %8, ptr getelementptr inbounds (i8, ptr @__profc_callee, i64 8), align 8
  store i32 1, ptr %2, align 4
  br label %10

9:                                                ; preds = %1
  store i32 0, ptr %2, align 4
  br label %10

10:                                               ; preds = %9, %7
  %11 = load i32, ptr %2, align 4
  ret i32 %11
}

; Function Attrs: nounwind
declare void @llvm.instrprof.increment(ptr, i64, i32, i32) #1

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @caller() #0 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  %pgocount = load i64, ptr @__profc_caller, align 8
  %3 = add i64 %pgocount, 1
  store i64 %3, ptr @__profc_caller, align 8
  store i32 0, ptr %1, align 4
  store i32 0, ptr %2, align 4
  br label %4

4:                                                ; preds = %15, %0
  %5 = load i32, ptr %2, align 4
  %6 = icmp ne i32 %5, 2
  br i1 %6, label %7, label %18

7:                                                ; preds = %4
  %pgocount1 = load i64, ptr getelementptr inbounds (i8, ptr @__profc_caller, i64 8), align 8
  %8 = add i64 %pgocount1, 1
  store i64 %8, ptr getelementptr inbounds (i8, ptr @__profc_caller, i64 8), align 8
  %9 = load volatile ptr, ptr @Target, align 8
  %10 = load i32, ptr %2, align 4
  %11 = ptrtoint ptr %9 to i64
  call void @__llvm_profile_instrument_target(i64 %11, ptr @__profd_caller, i32 0)
  %12 = call i32 %9(i32 noundef %10)
  %13 = load i32, ptr %1, align 4
  %14 = add i32 %13, %12
  store i32 %14, ptr %1, align 4
  br label %15

15:                                               ; preds = %7
  %16 = load i32, ptr %2, align 4
  %17 = add i32 %16, 1
  store i32 %17, ptr %2, align 4
  br label %4, !llvm.loop !11

18:                                               ; preds = %4
  %19 = load i32, ptr %1, align 4
  ret i32 %19
}

; Function Attrs: nounwind
declare void @llvm.instrprof.value.profile(ptr, i64, i64, i32, i32) #1

; Function Attrs: noinline noprofile nounwind optnone uwtable
define dso_local i32 @main() #2 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  store i32 0, ptr %1, align 4
  store i32 0, ptr %2, align 4
  br label %3

3:                                                ; preds = %15, %0
  %4 = load i32, ptr %2, align 4
  %5 = icmp ne i32 %4, 3
  br i1 %5, label %6, label %18

6:                                                ; preds = %3
  call void @__llvm_profile_reset_counters()
  %7 = call i32 @caller()
  %8 = icmp ne i32 %7, 1
  br i1 %8, label %13, label %9

9:                                                ; preds = %6
  %10 = call i32 @__llvm_profile_dump()
  %11 = icmp ne i32 %10, 0
  br i1 %11, label %13, label %12

12:                                               ; preds = %9
  br label %14

13:                                               ; preds = %9, %6
  store i32 1, ptr %1, align 4
  br label %19

14:                                               ; preds = %12
  br label %15

15:                                               ; preds = %14
  %16 = load i32, ptr %2, align 4
  %17 = add i32 %16, 1
  store i32 %17, ptr %2, align 4
  br label %3, !llvm.loop !13

18:                                               ; preds = %3
  store i32 0, ptr %1, align 4
  br label %19

19:                                               ; preds = %18, %13
  %20 = load i32, ptr %1, align 4
  ret i32 %20
}

declare dso_local void @__llvm_profile_reset_counters() #3

declare dso_local i32 @__llvm_profile_dump() #3

; Function Attrs: noinline
define linkonce_odr hidden i32 @__llvm_profile_runtime_user() #4 comdat !prof !14 {
  %1 = load i32, ptr @__llvm_profile_runtime, align 4
  ret i32 %1
}

declare void @__llvm_profile_instrument_target(i64, ptr, i32)

attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="reserved" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="generic" "target-features"="+fp-armv8,+neon,+v8a,-fmv" }
attributes #1 = { nounwind }
attributes #2 = { noinline noprofile nounwind optnone uwtable "frame-pointer"="reserved" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="generic" "target-features"="+fp-armv8,+neon,+v8a,-fmv" }
attributes #3 = { "frame-pointer"="reserved" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="generic" "target-features"="+fp-armv8,+neon,+v8a,-fmv" }
attributes #4 = { noinline }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5, !6}
!llvm.linker.options = !{!7, !8, !9}
!llvm.ident = !{!10}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "clang version 23.1.4 (https://github.com/llvm/llvm-project 7a941dfb2877a0b8cf30323fefa85ad019e0b0f5)", isOptimized: false, runtimeVersion: 0, emissionKind: NoDebug, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "instrprof-record-padding.c", directory: ".")
!2 = !{i32 2, !"EnableValueProfiling", i32 1}
!3 = !{i32 2, !"Debug Info Version", i32 3}
!4 = !{i32 8, !"PIC Level", i32 2}
!5 = !{i32 7, !"uwtable", i32 2}
!6 = !{i32 7, !"frame-pointer", i32 3}
!7 = !{!"/DEFAULTLIB:clang_rt.profile.lib"}
!8 = !{!"/DEFAULTLIB:msvcrt.lib"}
!9 = !{!"/DEFAULTLIB:oldnames.lib"}
!10 = !{!"clang version 23.1.4 (https://github.com/llvm/llvm-project 7a941dfb2877a0b8cf30323fefa85ad019e0b0f5)"}
!11 = distinct !{!11, !12}
!12 = !{!"llvm.loop.mustprogress"}
!13 = distinct !{!13, !12}
!14 = !{!"function_entry_count", i64 0}
