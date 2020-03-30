#!/bin/bash

# MUST BE RUN FROM APP ROOT
JOB=$1
NAME=Splunk_TA_paloalto
VERSION=`grep -o '^version = [0-9a-z.-]*' default/app.conf | awk '{print $3}'`
if [ "${TRAVIS}" == "true" ]; then
    BUILD=${TRAVIS_BUILD_NUMBER}
    BRANCH=${TRAVIS_BRANCH}
else
    BUILD="local"
    BRANCH=`git rev-parse --abbrev-ref HEAD`
fi
FILE="_build/${NAME}-${VERSION}-${BRANCH}-${BUILD}.tgz"
echo "AppInspect ${NAME} ${VERSION} build ${BUILD} for SplunkBase"
echo "File $FILE"

app_inspect_api() {
    request_id=$1
    type=$2
    echo $request_id $type
    if [ "$type" == "status" ]; then
        content=''
        url="https://appinspect.splunk.com/v1/app/validate/status/$request_id"
    fi
    if [ "$type" == "report" ]; then
        url="https://appinspect.splunk.com/v1/app/report/$request_id"
        content=(-H "Content-Type: text/html")
    fi
    echo "Gettings response for appinspect id $request_id"
    response=$(curl -X GET -H "Authorization: bearer $TOKEN" ${content[@]} --url "$url")
        echo "$type" "$response"
}
if [ "$JOB" == "start" ]; then
    #Start Job
    start_job=$(curl -X POST \
        --url "https://appinspect.splunk.com/v1/app/validate" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Cache-Control: no-cache" \
        -F "included_tags=py3_migration" \
        -F "app_package=@\"$FILE\"")
    echo start_search $start_job
fi 
# if [ -z "$start_job.request_id" ]; then
if [ "$JOB" == "status" ]; then
    request_id=$2
    app_inspect_api $request_id "status"
fi

if [ "$JOB" == "report" ]; then
    request_id=$2
    app_inspect_api $request_id "report"
fi



