import hashlib
from compression import zstd
import tarfile
from pathlib import Path
import subprocess

name = "clang+llvm-23.1.4-aarch64-pc-windows-msvc.tar.zst"
archive = Path("tools.tar.zst")
subprocess.run(["curl.exe", "-fsSL", "--retry", "3", "-o", archive,
                "https://github.com/llvm/llvm-project/releases/download/llvmorg-23.1.4/" + name], check=True)
with archive.open("rb") as f:
    if hashlib.file_digest(f, "sha256").hexdigest() != "6a1f1a4eaa18c6b83d0c61c85813664143643fa7df3c11f49750773d560a2164":
        raise RuntimeError("LLVM release archive checksum mismatch")
with zstd.open(archive, "rb", options={zstd.DecompressionParameter.window_log_max: 30}) as stream, \
        tarfile.open(fileobj=stream, mode="r|") as tar:
    for member in tar:
        p = Path(member.name)
        parts = p.parts[1:]
        if parts[:1] == ("bin",) or parts[:2] == ("lib", "clang"):
            if not member.name.lower().endswith((".pdb", ".debug")):
                tar.extract(member, "release", filter="data")
archive.unlink()
