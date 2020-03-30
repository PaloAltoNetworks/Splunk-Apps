#!/bin/bash

# MUST BE RUN FROM APP ROOT

set -e
NAME=SplunkforPaloAltoNetworks
VERSION=`grep -o '^version = [0-9a-z.-]*' default/app.conf | awk '{print $3}'`
if [ "${TRAVIS}" == "true" ]; then
    BUILD=${TRAVIS_BUILD_NUMBER}
    BRANCH=${TRAVIS_BRANCH}
else
    BUILD="local"
    BRANCH=`git rev-parse --abbrev-ref HEAD`
fi
echo "Build ${NAME} ${VERSION} build ${BUILD} for SplunkBase"

# Create tar file of App
rm -rf _build/ 2>/dev/null
mkdir -p _build/
git archive --format=tar --prefix=${NAME}/ ${BRANCH} | gzip >_build/${NAME}-${VERSION}-${BUILD}-temp.tgz

# Uncompress the App
cd _build/
tar xzf ${NAME}-${VERSION}-${BUILD}-temp.tgz
rm ${NAME}-${VERSION}-${BUILD}-temp.tgz

# Strip out stuff that SplunkBase doesn't like
# such as hidden files and Makefiles
find . -type f -name ".*" -exec rm {} \;
find ${NAME}/bin -type f -name "*.py" -exec chmod +x {} \;
rm ${NAME}/Makefile
rm ${NAME}/bin/lib/pandevice/docs/Makefile
rm ${NAME}/bin/lib/pan-python/doc/Makefile
rm -rf ${NAME}/release

# Re-compress to tar file and clean up
tar czf ${NAME}-${VERSION}-${BRANCH}-${BUILD}.tgz ${NAME}
rm -rf ${NAME}

echo "SplunkBase package is ready."