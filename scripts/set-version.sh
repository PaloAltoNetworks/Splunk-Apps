#!/bin/bash

SCRIPT_BASE="$(cd "$( dirname "$0")" && pwd )"
ROOT=${SCRIPT_BASE}/..
# shellcheck source=/dev/null
source "$SCRIPT_BASE/log4bash.sh"
log_debug "DEBUG ENABLED"

# App and Add-on Directories
APP=SplunkforPaloAltoNetworks
ADDON=Splunk_TA_paloalto

# Files where version needs to be bumped
APPCONF=default/app.conf
README=README.md
APPMANIFEST=app.manifest
GLOBALCONFIG=appserver/static/js/build/globalConfig.json

# Exit immediatly if any command exits with a non-zero status
set -e

# Usage
print_usage() {
    echo "Set the app/add-on version"
    echo ""
    echo "Usage:"
    echo "  set-version.sh <new-version> [release-channel]"
    echo ""
    echo "Release channel can be 'default', 'beta', or 'alpha'."
    echo "If not specified, the default channel is used."
}

# if less than one arguments supplied, display usage
if [  $# -lt 1 ]
then
    print_usage
    exit 1
fi

# check whether user had supplied -h or --help . If yes display usage
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    print_usage
    exit 0
fi

TEMP_VERSION=${1/-alpha\./alpha}
NEW_VERSION=${TEMP_VERSION/-beta\./beta}
CHANNEL=${2:-default}

# Get the current version from the app
CURRENT_VERSION=$(grep -o '^version = [0-9a-z.-]*' "$ROOT/$APP/default/app.conf" | awk '{print $3}')
# Generate a build number
if [ "$TRAVIS" == "true" ]; then
    log_debug "Running in TravisCI"
    BUILD=${TRAVIS_BUILD_NUMBER}
    # BRANCH=${TRAVIS_BRANCH}
elif [ "$GITHUB_ACTIONS" == "true" ]; then
    log_debug "Running in GitHub Actions"
    BUILD=${GITHUB_RUN_ID}
    # BRANCH=${GITHUB_REF#refs/heads/}
else
    log_debug "Running outside of CI"
    BUILD=${NEW_VERSION//[.-]/}0
    # BRANCH=$(git rev-parse --abbrev-ref HEAD)
fi

case $CHANNEL in
  default)
    DEVSTATUS='Production\/Stable'
    ;;
  beta)
    DEVSTATUS='Beta'
    ;;
  alpha)
    DEVSTATUS='Alpha'
    ;;
  *)
    DEVSTATUS='Production\/Stable'
    ;;
esac

log_debug "Build number: $BUILD"
log_info "Changing version from $CURRENT_VERSION to $NEW_VERSION build $BUILD on channel $CHANNEL"

# In each of the following replacements, grep us run first to confirm the line
# exists in the file. If grep fails to find the line, the whole script stops
# with a return code of 1. After each grep, sed does the replacement.

# Set App versions
FILE="${ROOT}/${APP}/${APPCONF}"

log_debug "Set App ${APPCONF} version to ${NEW_VERSION}"
grep -E '^version = .+$' "$FILE" >/dev/null
sed -i.bak -E "s/version = .+/version = ${NEW_VERSION}/" "$FILE" && rm "${FILE}.bak"

log_debug "Set App ${APPCONF} build to ${BUILD}"
grep -E '^build = .+$' "$FILE" >/dev/null
sed -i.bak -E "s/build = .+/build = ${BUILD}/" "$FILE" && rm "${FILE}.bak"

log_debug "Set App ${APPCONF} add-on required version to ${NEW_VERSION}"
grep -E '^ta_dependency_version = .+$' "$FILE" >/dev/null
sed -i.bak -E "s/ta_dependency_version = .+/ta_dependency_version = ${NEW_VERSION}/" "$FILE" && rm "${FILE}.bak"

FILE="${ROOT}/${APP}/${README}"

log_debug "Set App ${README} version to ${NEW_VERSION}"
grep -E 'App Version:\*\* .+$' "$FILE" >/dev/null
sed -i.bak -E "s/App Version:\*\* .+/App Version:** ${NEW_VERSION}/" "$FILE" && rm "${FILE}.bak"

log_debug "Set App ${APP}/${README} add-on required version to ${NEW_VERSION}"
grep -E 'Splunk_TA_paloalto .+$' "$FILE" >/dev/null
sed -i.bak -E "s/Splunk_TA_paloalto .+/Splunk_TA_paloalto ${NEW_VERSION}/" "$FILE" && rm "${FILE}.bak"

FILE="${ROOT}/${APP}/${APPMANIFEST}"

log_debug "Set App ${APPMANIFEST} version to ${NEW_VERSION}"
grep -E '\"version\": .+' "$FILE" >/dev/null
sed -i.bak -E "s/version\": .+/version\": \"${NEW_VERSION}\"/" "$FILE" && rm "${FILE}.bak"

log_debug "Set Addon ${APPMANIFEST} development status to ${DEVSTATUS}"
grep -E '\"developmentStatus\": .+' "$FILE" >/dev/null
sed -i.bak -E "s/developmentStatus\": .+/developmentStatus\": \"${DEVSTATUS}\"/" "$FILE" && rm "${FILE}.bak"

# Set Add-on versions

FILE="${ROOT}/${ADDON}/${APPCONF}"

log_debug "Set Addon ${APPCONF} version to ${NEW_VERSION}"
grep -E '^version = .+$' "$FILE" >/dev/null
sed -i.bak -E "s/version = .+/version = ${NEW_VERSION}/" "$FILE" && rm "${FILE}.bak"

log_debug "Set Addon ${APPCONF} build to ${BUILD}"
grep -E '^build = .+$' "$FILE" >/dev/null
sed -i.bak -E "s/build = .+/build = ${BUILD}/" "$FILE" && rm "${FILE}.bak"

FILE="${ROOT}/${ADDON}/${APPMANIFEST}"

log_debug "Set Addon ${APPMANIFEST} version to ${NEW_VERSION}"
grep -E '\"version\": .+' "$FILE" >/dev/null
sed -i.bak -E "s/version\": .+/version\": \"${NEW_VERSION}\"/" "$FILE" && rm "${FILE}.bak"

log_debug "Set Addon ${APPMANIFEST} development status to ${DEVSTATUS}"
grep -E '\"developmentStatus\": .+' "$FILE" >/dev/null
sed -i.bak -E "s/developmentStatus\": .+/developmentStatus\": \"${DEVSTATUS}\"/" "$FILE" && rm "${FILE}.bak"

FILE="${ROOT}/${ADDON}/${README}"

log_debug "Set Addon ${README} Version to ${NEW_VERSION}"
grep -E 'Add-on Version:\*\* .+$' "$FILE" >/dev/null
sed -i.bak -E "s/Add-on Version:\*\* .+/Add-on Version:** ${NEW_VERSION}/" "$FILE" && rm "${FILE}.bak"

FILE="${ROOT}/${ADDON}/${GLOBALCONFIG}"

log_debug "Set Addon GlobalConfig Version to ${NEW_VERSION}"
grep -E '\"version\": .+' "$FILE" >/dev/null
sed -i.bak -E "s/version\": .+/version\": \"${NEW_VERSION}\",/" "$FILE" && rm "${FILE}.bak"