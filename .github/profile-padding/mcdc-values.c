#include <stdio.h>

int left(int x) { return x + 1; }
int right(int x) { return x + 2; }

int decide(int a, int b, int c) { return (a && b) || c; }

int main(int argc, char **argv) {
  int (*volatile target)(int) = argc > 1 ? right : left;
  int begin = argc > 1 ? 4 : 0;
  int sum = 0;
  for (int i = begin; i < begin + 4; ++i)
    sum += target(i) + decide((i >> 2) & 1, (i >> 1) & 1, i & 1);
  printf("%d\n", sum);
  return 0;
}
