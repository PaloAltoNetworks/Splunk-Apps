#!/usr/bin/env bash

# This script publishes the built .spl file to SplunkBase
# It is intended to be used in a CI/CD pipline

# Env Vars Required:
# 
# SPLUNK_USER
# SPLUNK_PASS

set -e

command -v jq >/dev/null 2>&1 || (echo >&2 "The program 'jq' is required, please install it on your system"; exit 1)

if [ -z "$SPLUNK_USER" ] || [ -z "$SPLUNK_PASS" ]; then
    echo "Required environment variables: SPLUNK_USER, SPLUNK_PASS"
    exit 1
fi

SCRIPT_BASE="$(cd "$( dirname "$0")" && pwd )"
ROOT=${SCRIPT_BASE}/..

# shellcheck source=/dev/null
source "$SCRIPT_BASE/log4bash.sh"
# shellcheck source=/dev/null
source "$SCRIPT_BASE/common.sh"

log_debug "DEBUG ENABLED"

## Print command usage
print_usage () {
    echo ""
    echo "Usage:"
    echo ""
    echo "publish.sh -a <APP NAME> [-v <version> | -f <FILENAME>]"
    echo ""
    echo "  -a What to inspect. Must be either 'app' or 'addon'."
    echo "  -v Version of spl package to look for in _build directory"
    echo "  -f File to submit for publication"
    echo ""
}

## Submits an app for publication
submit_for_publication () {
    local app_id=$1
    local app_path=$2
    local splunk_versions=$3
    local cim_versions=$4
    local filename
    local response
    local error
    filename=$(basename "$app_path")
    log_info "Submitting app for publication"
    # Uses bash with netrc to hide password from CLI: https://stackoverflow.com/a/33818945
    if ! response=$(curl -Ss -X POST \
     --netrc-file <(cat <<<"machine splunkbase.splunk.com login $SPLUNK_USER password $SPLUNK_PASS") \
     -H "Cache-Control: no-cache" \
     -F "app_package=@\"${app_path}\"" \
     -F "files[]=@\"${app_path}\"" \
     -F "filename=\"${filename}\"" \
     -F "splunk_versions=\"${splunk_versions}\"" \
     -F "cim_versions=\"${cim_versions}\"" \
     -F "visibility=true" \
     --url "https://splunkbase.splunk.com/api/v1/app/${app_id}/new_release/")
    then
        log_error "Error during submit API call: $response"
        exit 2
    fi
    error=$(echo "$response" | jq -r '.detail')
    if [ "$error" != "null" ]; then
        log_error "Error during submit API call: $response"
        exit 3
    fi
    error=$(echo "$response" | jq -r '.errors')
    if [ "$error" != "null" ]; then
        log_error "Error during submit API call: $response"
        exit 5
    fi
    echo "$response" | jq -r '.id'
}

## Check status of validation
check_status () {
    local package_id=$1
    local response
    local status
    log_debug "Checking status"
    # Uses bash with netrc to hide password from CLI: https://stackoverflow.com/a/33818945
    if ! response=$(curl -Ss -X GET \
     --netrc-file <(cat <<<"machine splunkbase.splunk.com login $SPLUNK_USER password $SPLUNK_PASS") \
     --url "https://splunkbase.splunk.com/api/v1/package/${package_id}/")
    then
        log_error "Error during check status API call: $response"
        exit 2
    fi
    status=$(echo "$response" | jq -r '.result')
    if [ "$status" != "pass" ]; then
        log_error "Error during check status API call: $response"
        exit 3
    fi
    echo "$response"
}

APP=''
APP_ID=''

while getopts a:fv:h FLAG; do
    case $FLAG in
        a)
        if [ "$OPTARG" == "app" ]; then
            APP=SplunkforPaloAltoNetworks
            APP_ID="491"
        elif [ "$OPTARG" == "addon" ]; then
            APP=Splunk_TA_paloalto
            APP_ID="2757"
        elif [ "$OPTARG" == "test" ]; then
            APP=Splunk_TA_paloalto
            APP_ID="5179"
        else
            log_error "Unknown argument: $OPTARG"
            exit 1
        fi
        ;;
        f)
        FILENAME="$OPTARG"
        ;;
        v)
        VERSION="$OPTARG"
        ;;
        h)
        print_usage
        exit 0
        ;;
        \?) #unrecognized option - show help
        print_usage
        exit 1
        ;;
    esac
done

# Get the current version from the app
BRANCH=$(get_branch)
BUILD=$(get_build)

log_debug "Publish ${APP} build ${BUILD} to SplunkBase"

SPLUNK_SUPPORTED=$(get_splunk_supported "$APP")
CIM_SUPPORTED=$(get_cim_supported "$APP")

# Determine the file to publish
if [ -z "$FILENAME" ]; then
    if [ -z "$VERSION" ]; then
        VERSION=$(get_version "$ROOT/$APP")
    fi
    FILENAME="${ROOT}/_build/$(get_build_filename "$APP" "$VERSION" "$BRANCH" "$BUILD")"
fi 
log_debug "File $FILENAME"

# Publish the app package
PACKAGE_ID=$(submit_for_publication "$APP_ID" "$FILENAME" "$SPLUNK_SUPPORTED" "$CIM_SUPPORTED")
log_debug "Package ID: $PACKAGE_ID"
if [ "$PACKAGE_ID" == "null" ]; then
    log_error "Request for publication failed"
    exit 2
fi

# Verify publication
STATUS=$(check_status "$PACKAGE_ID")
log_debug "End status: $STATUS"

log_success "Completed"
exit 0
