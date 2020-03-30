#!/bin/bash

# Requirements:
#
# brew install git git-flow
#
# MUST BE RUN FROM APP ROOT

set -e

display_usage() {
    echo "Bump the version, commit, and merge with master"
    echo -e "\nUsage:\ngithub.sh <new-app-version> <required-add-on-version> \n"
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
echo "Bumping version from ${CURRENT_VERSION} to ${VERSION}"
# Files where version needs to be bumped
APPCONF=default/app.conf
README=README.md

git checkout develop

# Release on GitHub
git flow release start "${VERSION}"

# Bump Versions
release/bumpversion.sh "${VERSION}" "${ADDON_VERSION}"

# Add and commit version bump
git add ${README}
git add ${APPCONF}
git commit -m "Bump version number to ${VERSION}"

# Finish up gitflow and merge back to develop and master
git flow release finish "${VERSION}"

echo "Git release is ready. You still need to push develop and master to origin with tags."
echo "eg. git push origin master develop ${VERSION}"