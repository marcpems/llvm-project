; ModuleID = 'ec'
source_filename = "probe.c"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-p:64:64-i32:32-i64:64-i128:128-n32:64-S128-Fn32"
target triple = "arm64ec-pc-windows-msvc19.52.37029"

$__llvm_profile_runtime_user = comdat any

@__llvm_profile_runtime = external hidden global i32
@__profc_ec_alpha = private global [1 x i64] zeroinitializer, section ".lprfc$M", align 8
@__profd_ec_alpha = private global { i64, i64, i64, i64, i64, ptr, ptr, i32, [3 x i16], i16, i32 } { i64 7502952456392707257, i64 24, i64 sub (i64 ptrtoint (ptr @__profc_ec_alpha to i64), i64 ptrtoint (ptr @__profd_ec_alpha to i64)), i64 0, i64 0, ptr @ec_alpha.local, ptr null, i32 1, [3 x i16] zeroinitializer, i16 0, i32 0 }, section ".lprfd$M", align 8
@__profc_ec_beta = private global [1 x i64] zeroinitializer, section ".lprfc$M", align 8
@__profd_ec_beta = private global { i64, i64, i64, i64, i64, ptr, ptr, i32, [3 x i16], i16, i32 } { i64 6833552153680032442, i64 24, i64 sub (i64 ptrtoint (ptr @__profc_ec_beta to i64), i64 ptrtoint (ptr @__profd_ec_beta to i64)), i64 0, i64 0, ptr @ec_beta.local, ptr null, i32 1, [3 x i16] zeroinitializer, i16 0, i32 0 }, section ".lprfd$M", align 8
@__profc_ec_dispatch = private global [2 x i64] zeroinitializer, section ".lprfc$M", align 8
@__profvp_ec_dispatch = private global [1 x i64] zeroinitializer, section ".lprfv$M", align 8
@__profd_ec_dispatch = private global { i64, i64, i64, i64, i64, ptr, ptr, i32, [3 x i16], i16, i32 } { i64 5995019357675163204, i64 856, i64 sub (i64 ptrtoint (ptr @__profc_ec_dispatch to i64), i64 ptrtoint (ptr @__profd_ec_dispatch to i64)), i64 0, i64 0, ptr @ec_dispatch.local, ptr @__profvp_ec_dispatch, i32 2, [3 x i16] [i16 1, i16 0, i16 0], i16 0, i32 0 }, section ".lprfd$M", align 8
@__llvm_prf_vnodes = private global [10 x { i64, i64, ptr }] zeroinitializer, section ".lprfnd$M", align 8
@__llvm_prf_nm = private constant [34 x i8] c"\1C x\DAKM\8EO\CC)\C8HdLM\8EOJ-\01\D3)\99\C5\05\89%\C9\19\00\94|\0Aj", section ".lprfn$M", align 1
@llvm.used = appending global [6 x ptr] [ptr @__llvm_profile_runtime_user, ptr @__profd_ec_alpha, ptr @__profd_ec_beta, ptr @__profd_ec_dispatch, ptr @__llvm_prf_vnodes, ptr @__llvm_prf_nm], section "llvm.metadata"

@ec_alpha.local = private alias i32 (i32), ptr @ec_alpha
@ec_beta.local = private alias i32 (i32), ptr @ec_beta
@ec_dispatch.local = private alias i32 (i32, i32), ptr @ec_dispatch

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @ec_alpha(i32 noundef %0) #0 {
  %2 = alloca i32, align 4
  store i32 %0, ptr %2, align 4
  %pgocount = load i64, ptr @__profc_ec_alpha, align 8
  %3 = add i64 %pgocount, 1
  store i64 %3, ptr @__profc_ec_alpha, align 8
  %4 = load i32, ptr %2, align 4
  %5 = mul i32 %4, 33
  %6 = add i32 %5, 1
  ret i32 %6
}

; Function Attrs: nounwind
declare void @llvm.instrprof.increment(ptr, i64, i32, i32) #1

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @ec_beta(i32 noundef %0) #0 {
  %2 = alloca i32, align 4
  store i32 %0, ptr %2, align 4
  %pgocount = load i64, ptr @__profc_ec_beta, align 8
  %3 = add i64 %pgocount, 1
  store i64 %3, ptr @__profc_ec_beta, align 8
  %4 = load i32, ptr %2, align 4
  %5 = mul i32 %4, 33
  %6 = add i32 %5, 2
  ret i32 %6
}

; Function Attrs: noinline nounwind uwtable
define dso_local i32 @ec_dispatch(i32 noundef %0, i32 noundef %1) #0 {
  %3 = alloca i32, align 4
  %4 = alloca i32, align 4
  %5 = alloca ptr, align 8
  store i32 %1, ptr %3, align 4
  store i32 %0, ptr %4, align 4
  %pgocount = load i64, ptr @__profc_ec_dispatch, align 8
  %6 = add i64 %pgocount, 1
  store i64 %6, ptr @__profc_ec_dispatch, align 8
  call void @llvm.lifetime.start.p0(ptr %5) #1
  %7 = load i32, ptr %3, align 4
  %8 = icmp ne i32 %7, 0
  %9 = zext i1 %8 to i64
  %pgocount1 = load i64, ptr getelementptr inbounds (i8, ptr @__profc_ec_dispatch, i64 8), align 8
  %10 = add i64 %pgocount1, %9
  store i64 %10, ptr getelementptr inbounds (i8, ptr @__profc_ec_dispatch, i64 8), align 8
  %11 = select i1 %8, ptr @ec_alpha, ptr @ec_beta
  store volatile ptr %11, ptr %5, align 8
  %12 = load volatile ptr, ptr %5, align 8
  %13 = load i32, ptr %4, align 4
  %14 = ptrtoint ptr %12 to i64
  call void @__llvm_profile_instrument_target(i64 %14, ptr @__profd_ec_dispatch, i32 0)
  %15 = call i32 %12(i32 noundef %13)
  call void @llvm.lifetime.end.p0(ptr %5) #1
  ret i32 %15
}

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.start.p0(ptr captures(none)) #2

; Function Attrs: nounwind
declare void @llvm.instrprof.increment.step(ptr, i64, i32, i32, i64) #1

; Function Attrs: nounwind
declare void @llvm.instrprof.value.profile(ptr, i64, i64, i32, i32) #1

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.end.p0(ptr captures(none)) #2

; Function Attrs: noinline
define linkonce_odr hidden i32 @__llvm_profile_runtime_user() #3 comdat !prof !12 {
  %1 = load i32, ptr @__llvm_profile_runtime, align 4
  ret i32 %1
}

declare void @__llvm_profile_instrument_target(i64, ptr, i32)

attributes #0 = { noinline nounwind uwtable "frame-pointer"="reserved" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="generic" "target-features"="+fp-armv8,+neon,+v8a,-fmv" }
attributes #1 = { nounwind }
attributes #2 = { nocallback nofree nosync nounwind willreturn memory(argmem: readwrite) }
attributes #3 = { noinline }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5, !6}
!llvm.linker.options = !{!7, !8, !9, !10}
!llvm.ident = !{!11}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "clang version 23.1.4 (https://github.com/llvm/llvm-project 7a941dfb2877a0b8cf30323fefa85ad019e0b0f5)", isOptimized: true, runtimeVersion: 0, emissionKind: NoDebug, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "probe.c", directory: ".")
!2 = !{i32 2, !"EnableValueProfiling", i32 1}
!3 = !{i32 2, !"Debug Info Version", i32 3}
!4 = !{i32 8, !"PIC Level", i32 2}
!5 = !{i32 7, !"uwtable", i32 2}
!6 = !{i32 7, !"frame-pointer", i32 3}
!7 = !{!"/DEFAULTLIB:clang_rt.profile.lib"}
!8 = !{!"/DEFAULTLIB:libcmt.lib"}
!9 = !{!"/DEFAULTLIB:oldnames.lib"}
!10 = !{!"/DEFAULTLIB:softintrin.lib"}
!11 = !{!"clang version 23.1.4 (https://github.com/llvm/llvm-project 7a941dfb2877a0b8cf30323fefa85ad019e0b0f5)"}
!12 = !{!"function_entry_count", i64 0}
