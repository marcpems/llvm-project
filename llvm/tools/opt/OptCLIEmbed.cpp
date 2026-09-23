//===- OptCLIEmbed.cpp - Re-callable opt entrypoint for lit workers -------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#if defined(_WIN32)
#define LLVM_TOOL_EMBED_EXPORT __declspec(dllexport)
#else
#define LLVM_TOOL_EMBED_EXPORT __attribute__((visibility("default")))
#endif

int optMainEmbeddedImpl(int argc, char **argv);

extern "C" LLVM_TOOL_EMBED_EXPORT int OptMain(int argc, char **argv) {
  return optMainEmbeddedImpl(argc, argv);
}
