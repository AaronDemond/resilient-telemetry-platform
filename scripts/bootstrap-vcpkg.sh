#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/.." && pwd)"
vcpkg_root="${VCPKG_ROOT:-${repo_root}/vcpkg}"

echo "Bootstrapping vcpkg at ${vcpkg_root}"

if [[ ! -d "${vcpkg_root}" ]]; then
  echo "Cloning vcpkg into ${vcpkg_root}"
  git clone https://github.com/microsoft/vcpkg.git "${vcpkg_root}"
fi

"${vcpkg_root}/bootstrap-vcpkg.sh" -disableMetrics

echo "VCPKG_ROOT=${vcpkg_root}" >> "${GITHUB_ENV}"