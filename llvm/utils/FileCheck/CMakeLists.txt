add_llvm_utility(FileCheck
  FileCheck.cpp

  PARTIAL_SOURCES_INTENDED
  )

target_link_libraries(FileCheck PRIVATE LLVMFileCheck LLVMSupport)

# Experimental: a shared library exposing FileCheckMain(argc, argv), built
# from an unmodified copy of FileCheck.cpp's CLI driver body (just renamed
# and made safely re-callable), so it can be loaded once per lit worker
# process via ctypes and called in-process for every FileCheck RUN line
# instead of spawning FileCheck.exe each time. See
# lit/builtin_commands/filecheck_dll.py and marcpems/llvm-win-wsl-perf-bench
# for the motivating measurement. Windows-only: this is where the
# CreateProcess cost this avoids is highest, and FileCheckMain's fd-based
# stdout/stderr capture (os.dup2 in filecheck_dll.py) is only wired up for
# Windows so far.
#
# PARTIAL_SOURCES_INTENDED is required on both targets here because LLVM's
# build system otherwise enforces exactly one target per directory listing
# all of that directory's source files; FileCheckCLIEmbed.cpp deliberately
# is *not* part of the FileCheck target above (it's a separate DLL, not
# linked into FileCheck.exe).
if(WIN32)
  add_llvm_library(FileCheckEmbedCLI SHARED
    FileCheckCLIEmbed.cpp

    PARTIAL_SOURCES_INTENDED
    )

  target_link_libraries(FileCheckEmbedCLI PRIVATE LLVMFileCheck LLVMSupport)
endif()

