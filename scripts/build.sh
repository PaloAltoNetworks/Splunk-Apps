#!/bin/bash

SCRIPT_BASE="$(cd "$( dirname "$0")" && pwd )"
ROOT=${SCRIPT_BASE}/..

# shellcheck source=/dev/null
source "$SCRIPT_BASE/log4bash.sh"
# shellcheck source=/dev/null
source "$SCRIPT_BASE/common.sh"

# Exit immediatly if any command exits with a non-zero status
set -e

## Print command usage
print_usage () {
    echo ""
    echo "Usage:"
    echo ""
    echo "build.sh -a <app or addon>"
    echo ""
    echo "  -a What to build. Must be either 'app' or 'addon'."
    echo ""
}

APP='Splunk_TA_paloalto'

while getopts a:h FLAG; do
  case $FLAG in
    a)
      if [ "$OPTARG" == "app" ]; then
        APP=SplunkforPaloAltoNetworks
      elif [ "$OPTARG" == "addon" ]; then
        APP=Splunk_TA_paloalto
      else
        log_error "Unknown argument: $OPTARG"
        exit 1
      fi
      ;;
    h)
      print_usage
      ;;
    \?) #unrecognized option - show help
      print_usage
      exit 1
      ;;
  esac
done

# Get the current version from the app
VERSION=$(get_version "$ROOT/$APP")
BRANCH=$(get_branch)
BUILD=$(get_build)

log_info "Building ${APP} version ${VERSION} build ${BUILD} from branch ${BRANCH}"

# Create tar file of App
rm -rf "${ROOT}/_build/tmp" 2>/dev/null
mkdir -p "${ROOT}/_build/tmp"
cd "${ROOT}/${APP}"
git archive --format=tar --prefix="${APP}/" HEAD ./ | gzip >"${ROOT}/_build/tmp/${APP}-${VERSION}-${BUILD}-temp.tgz"

# Uncompress the App
cd "${ROOT}/_build/tmp"
rm -rf "${APP}" >/dev/null
tar xzf "${APP}-${VERSION}-${BUILD}-temp.tgz"
rm "${APP}-${VERSION}-${BUILD}-temp.tgz"

# Strip out stuff that SplunkBase doesn't like
# such as hidden files and Makefiles
find . -type f -name ".*" -exec rm {} \;
find "${APP}/bin" -type f -name "*.py" -exec chmod +x {} \;
rm "${APP}/Makefile"
rm "${APP}/bin/lib/pandevice/docs/Makefile"
rm "${APP}/bin/lib/pan-python/doc/Makefile"
rm -rf "${APP}/release"

FILENAME=$(get_build_filename "$APP" "$VERSION" "$BRANCH" "$BUILD")

# Re-compress to tar file and clean up
tar czf "${ROOT}/_build/${FILENAME}" "${APP}"

# Set variables for GitHub Actions to pick up in subsequent steps
if [ "$GITHUB_ACTIONS" == "true" ]; then
    echo ::set-output "name=path::_build/${FILENAME}"
    echo ::set-output "name=file::${FILENAME}"
fi

# Cleanup
cd "${ROOT}"
rm -rf "${ROOT}/_build/tmp"

log_success "SplunkBase package is ready."