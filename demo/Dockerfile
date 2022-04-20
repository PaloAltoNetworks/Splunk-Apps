FROM splunk/splunk:8.2.5
LABEL authors "Brian Torres-Gil <brian@ixi.us>,Paul Nguyen <panguyen@paloaltonetworks.com>"

USER root

# Install GCC to build eventgen
RUN microdnf install gcc-c++ gcc

# Download a stable Eventgen
RUN wget -qO /tmp/eventgen.tar.gz https://github.com/splunk/eventgen/archive/7.2.1.tar.gz
RUN tar -xzf /tmp/eventgen.tar.gz -C /tmp/
RUN mv /tmp/eventgen-7.2.1 /tmp/eventgen
RUN rm -f /tmp/eventgen.tar.gz
# Build eventgen per instructions here:
# https://github.com/splunk/eventgen/blob/develop/docs/SETUP.md#splunk-app-installation--first-run
RUN cd /tmp/eventgen; /opt/splunk/bin/python3 -m splunk_eventgen build --destination /tmp/eventgen-build
RUN mv /tmp/eventgen-build/sa_eventgen_Unknown.spl /tmp/eventgen.tgz

# Load eventgen configuration
COPY demo/samples /tmp/datagen/samples
COPY demo/conf/eventgen_conf/eventgen.conf /tmp/datagen/default/eventgen.conf
COPY demo/conf/eventgen_conf/eventgen.conf.spec /tmp/datagen/README/eventgen.conf.spec
COPY demo/conf/eventgen_conf/eventgen_kvstore_loader.py /tmp/datagen/bin/eventgen_kvstore_loader.py

# Splunk configuration
ENV SPLUNK_START_ARGS --accept-license
ENV SPLUNK_APPS_URL "/tmp/splunk/_build/SplunkforPaloAltoNetworks.tgz,/tmp/splunk/_build/Splunk_TA_paloalto.tgz,/tmp/eventgen.tgz"
COPY demo/setup_demo.yml /tmp/setup_demo.yml
COPY demo/default.yml /tmp/defaults/default.yml

# Build app and add-on
COPY Splunk_TA_paloalto /tmp/splunk/Splunk_TA_paloalto
COPY SplunkforPaloAltoNetworks /tmp/splunk/SplunkforPaloAltoNetworks
COPY scripts /tmp/splunk/scripts
RUN /tmp/splunk/scripts/build.sh -a app -o SplunkforPaloAltoNetworks.tgz -l
RUN /tmp/splunk/scripts/build.sh -a addon -o Splunk_TA_paloalto.tgz -l

# Ports Splunk Web, Splunk Daemon, KVStore, Splunk Indexing Port, Network Input, HTTP Event Collector
EXPOSE 8000/tcp 8089/tcp 8191/tcp 9997/tcp 1514 8088/tcp

WORKDIR /opt/splunk

# Configurations folder, var folder for everything (indexes, logs, kvstore)
VOLUME [ "/opt/splunk/etc", "/opt/splunk/var" ]

ENTRYPOINT ["/sbin/entrypoint.sh"]
CMD ["start-service"]
