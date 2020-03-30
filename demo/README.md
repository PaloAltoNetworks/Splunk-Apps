Palo Alto Networks Splunk App Demo for Docker
=============================================

## Information

A docker image containing Splunk that runs the latest Palo Alto Networks Splunk app.  The image also containes Splunk EventGen App to generate data. The EventGen is on by default. To disable it, disable the `SA_Eventgen` app in splunk.

## Install or Upgrade

Assuming you have [docker](https://www.docker.com) installed...

Use these same commands for installing the demo or upgrading an existing demo.

**Create and go to the demo directory**

Start by creating a directory for the demo files. (You can place the files anywhere, but in this example we'll place them in `/opt/splunk-demo`)

    mkdir /opt/splunk-demo     # this command not needed for upgrades
    cd /opt/splunk-demo

**Install the demo on Ubuntu or Kali Linux**

From inside the demo directory you created, type this command to install or upgrade the Palo Alto Networks Splunk app demo:

    curl -sSL http://bit.ly/splunk-panw-demo | sh

## Splunk Login

    Default login is admin:paloalto

## Start and stop

After installation, the server is running.

**Stop the Splunk server**

    docker stop splunk-demo

**Start the Splunk server**

    docker start splunk-demo

## Uninstall

**Remove the running demo container**

    docker rm -fv splunk-demo

**Remove the base image**

    docker rmi btorresgil/splunk-panw-demo

**Remove the demo files**

    # assuming the files are in /opt/splunk-demo
    rm -rf /opt/splunk-demo

## License

You can run the demo unlicnesed or with a license.

**Unlicensed**

500 MB can be indexed per day.  This is usually fine for short demos.

**Licensed**

10 GB indexed per day with a free license from the [Splunk Developer Portal](http://dev.splunk.com/page/developer_license_sign_up). This is useful for longer running servers, or servers that need to receive lots of logs from a live firewall:

To install the license, in the Splunk GUI go to Settings -> Licensing

After the server is licensed, it will make you login to the web gui.  The default credentials are admin/paloalto.

## Support

This image is supported on a best-effort basis.  Please report any issues here:

https://github.com/btorresgil/docker-splunk-panw-demo/issues

## More information

See the README for the base Splunk docker image for more information on available volumes and environment variables:
https://github.com/splunk/docker-splunk/tree/master/enterprise
