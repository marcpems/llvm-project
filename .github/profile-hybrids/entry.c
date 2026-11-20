int leaf(int);
int main(void) {
  int total = 0;
  for (int i = 0; i != 3; ++i)
    total += leaf(i);
  return total != 5;
}
