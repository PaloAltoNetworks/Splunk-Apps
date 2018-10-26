#!/bin/bash

# MUST BE RUN FROM APP ROOT

set -e

display_usage() {
    echo "Bump the version"
    echo -e "\nUsage:\nbumpversion.sh <new-app-version> <required-add-on-version> \n"
}

# if less than two arguments supplied, display usage
if [  $# -le 1 ]
then
    display_usage
    exit 1
fi

# check whether user had supplied -h or --help . If yes display usage
if [[ ( $# == "--help") ||  $# == "-h" ]]
then
    display_usage
    exit 0
fi

VERSION=$1
ADDON_VERSION=$2
CURRENT_VERSION=`grep -o '^version = [0-9a-z.-]*' default/app.conf | awk '{print $3}'`
BUILD=${VERSION//./}0
echo "Bumping version from ${CURRENT_VERSION} to ${VERSION} build ${BUILD}"
# Files where version needs to be bumped
APPCONF=default/app.conf
README=README.md

# Bump Versions
sed -i '' -E 's/version = .+/version = '${VERSION}'/' ${APPCONF} ${APPCONF}
echo "Bump ${APPCONF} version to ${VERSION}"
sed -i '' -E 's/build = .+/build = '${BUILD}'/' ${APPCONF} ${APPCONF}
echo "Bump ${APPCONF} build to ${BUILD}"
sed -i '' -E 's/ta_dependency_version = .+/ta_dependency_version = '${ADDON_VERSION}'/' ${APPCONF} ${APPCONF}
echo "Bump ${APPCONF} add-on required version to ${ADDON_VERSION}"
sed -i '' -E 's/App Version:\*\* .+/App Version:** '${VERSION}'/' ${README} ${README}
echo "Bump ${README} Version to ${VERSION}"
sed -i '' -E 's/Splunk_TA_paloalto .+/Splunk_TA_paloalto '${ADDON_VERSION}'/' ${README} ${README}
echo "Bump ${README} add-on required version to ${ADDON_VERSION}"


