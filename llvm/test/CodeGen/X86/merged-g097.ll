; RUN: llc -mtriple=x86_64-unknown-linux-gnu -stop-after=finalize-isel < %s | FileCheck %s

; ---- from atomic-mmo-align.ll ----
; The IR-specified alignment on atomicrmw / cmpxchg must be carried into the
; MachineMemOperand, matching the atomic load/store paths in
; SelectionDAGBuilder (which use I.getAlign()).  Previously visitAtomicRMW and
; visitAtomicCmpXchg used getEVTAlign(MemVT) (the natural type alignment),
; silently discarding an over-aligned `align N`.

define i32 @rmw_align_g97m0(ptr %p) {
  ; CHECK-LABEL: name: rmw_align_g97m0
  ; CHECK: LXADD32 {{.*}} :: (load store seq_cst (s32) on %ir.p, align 32)
  %r = atomicrmw add ptr %p, i32 1 seq_cst, align 32
  ret i32 %r
}

define i32 @cas_align_g97m0(ptr %p, i32 %c, i32 %n) {
  ; CHECK-LABEL: name: cas_align_g97m0
  ; CHECK: LCMPXCHG32 {{.*}} :: (load store seq_cst seq_cst (s32) on %ir.p, align 32)
  %r = cmpxchg ptr %p, i32 %c, i32 %n seq_cst seq_cst, align 32
  %v = extractvalue { i32, i1 } %r, 0
  ret i32 %v
}

; ---- from reset-fpenv-mmo.ll ----
; LowerRESET_FPENV builds a MachineMemOperand for the constant-pool blob it
; loads via FLDENVm. The flag must be MOLoad: FLDENVm is mayLoad = 1, so a
; MOStore-flagged MMO is silently dropped by SelectionDAGISel's memref
; filter, leaving FLDENVm with no memrefs at all. Verify the load-direction
; MMO survives to the final MachineInstr.

declare void @llvm.reset.fpenv()

define void @reset_fpenv_mmo_g97m1() nounwind {
  ; CHECK-LABEL: name: reset_fpenv_mmo_g97m1
  ; CHECK: FLDENVm {{.*}} :: (load (s224) from constant-pool, align 4)
  ; CHECK-NEXT: LDMXCSR {{.*}} implicit-def dead $mxcsr
  ; CHECK-NEXT: RET 0
  call void @llvm.reset.fpenv()
  ret void
}
