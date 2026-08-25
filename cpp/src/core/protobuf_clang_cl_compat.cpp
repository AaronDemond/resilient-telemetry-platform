// clang-cl decorates __restrict in this Protobuf extern-template symbol, while
// the MSVC-built vcpkg archive exports the undecorated pointer signature.
#include <google/protobuf/repeated_ptr_field.h>

namespace google::protobuf::internal {

template void memswap<ArenaOffsetHelper<RepeatedPtrFieldBase>::value>(
    char* __restrict,
    char* __restrict);

}  // namespace google::protobuf::internal