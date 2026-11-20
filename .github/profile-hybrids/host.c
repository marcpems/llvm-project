#include <windows.h>
#include <stdlib.h>

int main(int argc, char **argv) {
  if (argc != 3) return 1;
  HMODULE h = LoadLibraryA(argv[1]);
  if (!h) return 2;
  int (*view)(void) = (void *)GetProcAddress(h, "view_id");
  unsigned (*run)(unsigned, int) = (void *)GetProcAddress(h, "run");
  unsigned long long (*bytes)(void) = (void *)GetProcAddress(h, "bytes");
  int (*serialize)(char *) = (void *)GetProcAddress(h, "serialize");
  if (!view || view() != atoi(argv[2]) || !run || !bytes || !serialize) return 3;
  unsigned x = 1, check = 1;
  for (int i = 0; i != 7; ++i) {
    x = run(x, i % 3 != 0);
    check = check * 33u + (i % 3 ? 1 : 2);
  }
  unsigned long long n = bytes();
  char *buffer = malloc(n);
  if (!n || !buffer || serialize(buffer) || x != check) return 4;
  free(buffer);
  return 0;
}
