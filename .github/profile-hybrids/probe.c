#define CAT_(a,b) a##b
#define CAT(a,b) CAT_(a,b)
#define FN(x) CAT(VIEW,x)

__declspec(noinline) unsigned FN(_alpha)(unsigned x) { return x * 33u + 1; }
__declspec(noinline) unsigned FN(_beta)(unsigned x) { return x * 33u + 2; }

__declspec(noinline) unsigned FN(_dispatch)(unsigned x, int which) {
    unsigned (*volatile f)(unsigned) = which ? FN(_alpha) : FN(_beta);
    return f(x);
}
