#!/bin/bash

# MUST BE RUN FROM APP ROOT

set -e

display_usage() {
    echo "Bump the version"
    echo -e "\nUsage:\nbumpversion.sh <new-addon-version> \n"
}

# if less than two arguments supplied, display usage
if [  $# -le 0 ]
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
CURRENT_VERSION=`grep -o '^version = [0-9a-z.-]*' default/app.conf | awk '{print $3}'`
BUILD=${VERSION//./}0
echo "Bumping version from ${CURRENT_VERSION} to ${VERSION} build ${BUILD}"
# Files where version needs to be bumped
APPCONF=default/app.conf
APPMANIFEST=app.manifest
README=README.md

# Bump Versions
sed -i '' -E 's/version = .+/version = '${VERSION}'/' ${APPCONF} ${APPCONF}
echo "Bump ${APPCONF} version to ${VERSION}"
sed -i '' -E 's/version": .+/version": '\"${VERSION}\"'/' ${APPMANIFEST} ${APPMANIFEST}
echo "Bump ${APPMANIFEST} version to ${VERSION}"
sed -i '' -E 's/build = .+/build = '${BUILD}'/' ${APPCONF} ${APPCONF}
echo "Bump ${APPCONF} build to ${BUILD}"
sed -i '' -E 's/Add-on Version:\*\* .+/Add-on Version:** '${VERSION}'/' ${README} ${README}
echo "Bump ${README} Version to ${VERSION}"


