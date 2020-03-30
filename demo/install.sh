#!/bin/sh

##
## This installer works on Ubuntu and Kali Linux
##
## Problems with this script?  Contact btorres-gil@paloaltonetworks.com
##

# Check that docker is installed
command -v docker >/dev/null 2>&1 || { echo >&2 "Docker is not installed yet.  Aborting."; exit 1; }

# Check if a system-local directory exists
# This determines if fresh install or existing install
if [ -d "$PWD/system-local" ]; then
    echo "Found existing Splunk config in local directory. Performing upgrade."
    rm -rf db system-local users-local auth-local app-local datagen-local
fi

# Destroy any current splunk-demo
docker rm -fv splunk-demo >/dev/null 2>&1

# docker pull latest version of demo
docker pull btorresgil/splunk-panw-demo

# docker rmi <none> images
docker rmi $(docker images -f "dangling=true" -q) >/dev/null 2>&1

# docker run w/ many volumes in the local directory
docker run -d --name splunk-demo \
    -p 8000:8000 \
    -p 514:514/udp \
    -p 514:514 \
    -v $PWD/etc:/opt/splunk/etc \
    -v $PWD/var:/opt/splunk/var \
    -v /etc/localtime:/etc/localtime:ro \
    btorresgil/splunk-panw-demo

# Create an upgrade script
echo "#!/bin/sh" > ${PWD}/upgrade.sh
echo "cd ${PWD}" >> ${PWD}/upgrade.sh
echo "curl -sSL http://bit.ly/splunk-panw-demo | sudo sh" >> ${PWD}/upgrade.sh
chmod +x ${PWD}/upgrade.sh

# Create an start script
echo "#!/bin/sh" > ${PWD}/start.sh
echo "service docker start" >> ${PWD}/start.sh
echo "docker start splunk-demo" >> ${PWD}/start.sh
chmod +x ${PWD}/start.sh

# Get the Splunk icon
curl --silent -o ${PWD}/splunk_icon.png "https://raw.githubusercontent.com/btorresgil/docker-splunk-panw-demo/master/splunk_icon.png"

# Create an upgrade and start script on the desktop if there is a desktop

if [ -d "${HOME}/Desktop" ]; then
    SHORTCUT="${HOME}/Desktop/Upgrade Splunk App.desktop"
    echo "[Desktop Entry]" > ${SHORTCUT}
    echo "Type=Application" >> ${SHORTCUT}
    echo "Name=Upgrade Splunk App" >> ${SHORTCUT}
    echo "Exec=${PWD}/upgrade.sh" >> ${SHORTCUT}
    echo "Icon=${PWD}/splunk_icon.png" >> ${SHORTCUT}
    echo "Terminal=true" >> ${SHORTCUT}
    echo "Comment=Created by Splunk PANW Demo Installer" >> ${SHORTCUT}
    chmod +x "${SHORTCUT}"

    SHORTCUT="${HOME}/Desktop/Start Splunk.desktop"
    echo "[Desktop Entry]" > ${SHORTCUT}
    echo "Type=Application" >> ${SHORTCUT}
    echo "Name=Start Splunk" >> ${SHORTCUT}
    echo "Exec=${PWD}/start.sh" >> ${SHORTCUT}
    echo "Icon=${PWD}/splunk_icon.png" >> ${SHORTCUT}
    echo "Terminal=true" >> ${SHORTCUT}
    echo "Comment=Created by Splunk PANW Demo Installer" >> ${SHORTCUT}
    chmod +x "${SHORTCUT}"
fi

