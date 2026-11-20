; ModuleID = 'entry'
source_filename = "entry.c"
target datalayout = "e-m:w-p270:32:32-p271:32:32-p272:64:64-p:64:64-i32:32-i64:64-i128:128-n32:64-S128-Fn32"
target triple = "arm64ec-pc-windows-msvc19.52.37029"

$__llvm_profile_runtime_user = comdat any

@__llvm_profile_runtime = external hidden global i32
@__profc_main = private global [2 x i64] zeroinitializer, section ".lprfc$M", align 8
@__profd_main = private global { i64, i64, i64, i64, i64, ptr, ptr, i32, [3 x i16], i16, i32 } { i64 -2624081020897602054, i64 75568672, i64 sub (i64 ptrtoint (ptr @__profc_main to i64), i64 ptrtoint (ptr @__profd_main to i64)), i64 0, i64 0, ptr null, ptr null, i32 2, [3 x i16] zeroinitializer, i16 0, i32 0 }, section ".lprfd$M", align 8
@__llvm_prf_nm = private constant [14 x i8] c"\04\0Cx\DA\CBM\CC\CC\03\00\04\1B\01\A6", section ".lprfn$M", align 1
@llvm.compiler.used = appending global [2 x ptr] [ptr @__llvm_profile_runtime_user, ptr @__profd_main], section "llvm.metadata"
@llvm.used = appending global [1 x ptr] [ptr @__llvm_prf_nm], section "llvm.metadata"

; Function Attrs: nounwind uwtable
define dso_local i32 @main() #0 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  %3 = alloca i32, align 4
  store i32 0, ptr %1, align 4
  %pgocount = load i64, ptr @__profc_main, align 8
  %4 = add i64 %pgocount, 1
  store i64 %4, ptr @__profc_main, align 8
  call void @llvm.lifetime.start.p0(ptr %2) #1
  store i32 0, ptr %2, align 4
  call void @llvm.lifetime.start.p0(ptr %3) #1
  store i32 0, ptr %3, align 4
  br label %5

5:                                                ; preds = %15, %0
  %6 = load i32, ptr %3, align 4
  %7 = icmp ne i32 %6, 3
  br i1 %7, label %9, label %8

8:                                                ; preds = %5
  call void @llvm.lifetime.end.p0(ptr %3) #1
  br label %18

9:                                                ; preds = %5
  %pgocount1 = load i64, ptr getelementptr inbounds (i8, ptr @__profc_main, i64 8), align 8
  %10 = add i64 %pgocount1, 1
  store i64 %10, ptr getelementptr inbounds (i8, ptr @__profc_main, i64 8), align 8
  %11 = load i32, ptr %3, align 4
  %12 = call i32 @leaf(i32 noundef %11)
  %13 = load i32, ptr %2, align 4
  %14 = add i32 %13, %12
  store i32 %14, ptr %2, align 4
  br label %15

15:                                               ; preds = %9
  %16 = load i32, ptr %3, align 4
  %17 = add i32 %16, 1
  store i32 %17, ptr %3, align 4
  br label %5, !llvm.loop !12

18:                                               ; preds = %8
  %19 = load i32, ptr %2, align 4
  %20 = icmp ne i32 %19, 5
  %21 = zext i1 %20 to i32
  call void @llvm.lifetime.end.p0(ptr %2) #1
  ret i32 %21
}

; Function Attrs: nounwind
declare void @llvm.instrprof.increment(ptr, i64, i32, i32) #1

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.start.p0(ptr captures(none)) #2

declare dso_local i32 @leaf(i32 noundef) #3

; Function Attrs: nocallback nofree nosync nounwind willreturn memory(argmem: readwrite)
declare void @llvm.lifetime.end.p0(ptr captures(none)) #2

; Function Attrs: noinline
define linkonce_odr hidden i32 @__llvm_profile_runtime_user() #4 comdat !prof !14 {
  %1 = load i32, ptr @__llvm_profile_runtime, align 4
  ret i32 %1
}

attributes #0 = { nounwind uwtable "frame-pointer"="reserved" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="generic" "target-features"="+fp-armv8,+neon,+v8a,-fmv" }
attributes #1 = { nounwind }
attributes #2 = { nocallback nofree nosync nounwind willreturn memory(argmem: readwrite) }
attributes #3 = { "frame-pointer"="reserved" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="generic" "target-features"="+fp-armv8,+neon,+v8a,-fmv" }
attributes #4 = { noinline }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5, !6}
!llvm.linker.options = !{!7, !8, !9, !10}
!llvm.ident = !{!11}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "clang version 23.1.4 (https://github.com/llvm/llvm-project 7a941dfb2877a0b8cf30323fefa85ad019e0b0f5)", isOptimized: true, runtimeVersion: 0, emissionKind: NoDebug, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "entry.c", directory: ".")
!2 = !{i32 2, !"EnableValueProfiling", i32 0}
!3 = !{i32 2, !"Debug Info Version", i32 3}
!4 = !{i32 8, !"PIC Level", i32 2}
!5 = !{i32 7, !"uwtable", i32 2}
!6 = !{i32 7, !"frame-pointer", i32 3}
!7 = !{!"/DEFAULTLIB:clang_rt.profile.lib"}
!8 = !{!"/DEFAULTLIB:libcmt.lib"}
!9 = !{!"/DEFAULTLIB:oldnames.lib"}
!10 = !{!"/DEFAULTLIB:softintrin.lib"}
!11 = !{!"clang version 23.1.4 (https://github.com/llvm/llvm-project 7a941dfb2877a0b8cf30323fefa85ad019e0b0f5)"}
!12 = distinct !{!12, !13}
!13 = !{!"llvm.loop.mustprogress"}
!14 = !{!"function_entry_count", i64 0}
