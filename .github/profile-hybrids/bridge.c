#define CAT_(a,b) a##b
#define CAT(a,b) CAT_(a,b)
unsigned CAT(VIEW,_dispatch)(unsigned, int);
unsigned long long __llvm_profile_get_size_for_buffer(void);
int __llvm_profile_write_buffer(char *);
__declspec(dllexport) unsigned run(unsigned x, int which) { return CAT(VIEW,_dispatch)(x, which); }
__declspec(dllexport) unsigned long long bytes(void) { return __llvm_profile_get_size_for_buffer(); }
__declspec(dllexport) int serialize(char *buffer) { return __llvm_profile_write_buffer(buffer); }
__declspec(dllexport) int view_id(void) { return ID; }
