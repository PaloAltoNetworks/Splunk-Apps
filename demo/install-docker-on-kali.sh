# This script installs docker on the latest Kali Linux (or any Wheezy Debian distro)
# Updated 02/26/2018 for Kali 2017.3

# If this script breaks, please reach out to splunkapp@paloaltonetworks.com

# Update apt-get
export DEBIAN_FRONTEND="noninteractive"
/usr/bin/apt-get update
# Purge old docker
/usr/bin/apt-get purge -y -qq docker docker-engine "docker.io*" "lxc-docker*"
# Install dependencies
/usr/bin/apt-get install -y -q apt-transport-https ca-certificates curl gnupg2 software-properties-common
# Add docker repo gpg key and repo
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
echo "deb https://download.docker.com/linux/debian stretch stable" > /etc/apt/sources.list.d/docker.list
# Install Docker
/usr/bin/apt-get update
/usr/bin/apt-get install -y -q docker-ce
# Start docker on boot
systemctl enable docker
