#include <fstream>
#include <iostream>
#include <string>

#include "telemetry/v1/telemetry_message.pb.h"

namespace {

bool Require(bool condition, const std::string& message) {
  if (!condition) {
    std::cerr << "PYTHON_CPP_ROUNDTRIP_FAIL: " << message << '\n';
    return false;
  }
  return true;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 2) {
    std::cerr << "usage: python_to_cpp_roundtrip_test <serialized_message_path>\n";
    return 1;
  }

  std::ifstream input(argv[1], std::ios::binary);
  if (!input) {
    std::cerr << "Unable to open serialized message input\n";
    return 1;
  }

  std::string payload((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
  if (!Require(!payload.empty(), "Serialized payload was empty")) {
    return 1;
  }

  telemetry::v1::TelemetryMessage decoded;
  if (!Require(decoded.ParseFromString(payload), "Failed to parse serialized payload")) {
    return 1;
  }

  if (!Require(decoded.has_envelope(), "Decoded message missing envelope")) {
    return 1;
  }
  if (!Require(decoded.has_event(), "Decoded message missing event")) {
    return 1;
  }

  if (!Require(decoded.envelope().message_id() == "msg-python-roundtrip",
               "Decoded message_id mismatch")) {
    return 1;
  }
  if (!Require(decoded.envelope().unit_id() == "unit-python-roundtrip",
               "Decoded unit_id mismatch")) {
    return 1;
  }
  if (!Require(decoded.event().unit_id() == "unit-python-roundtrip",
               "Decoded event unit_id mismatch")) {
    return 1;
  }
  if (!Require(decoded.event().software_version() == "1.2.3",
               "Decoded software_version mismatch")) {
    return 1;
  }
  if (!Require(decoded.event().status() == telemetry::v1::UNIT_STATUS_AVAILABLE,
               "Decoded status mismatch")) {
    return 1;
  }

  // The round-trip contract is satisfied when the serialized bytes that came from
  // Python parse cleanly into the same logical message in C++.
  const std::string reserialized = decoded.SerializeAsString();
  if (!Require(reserialized == payload,
               "Re-serialized C++ payload does not match original Python protobuf payload")) {
    return 1;
  }

  std::cout << "Python-to-C++ telemetry protobuf round-trip OK\n";
  return 0;
}
