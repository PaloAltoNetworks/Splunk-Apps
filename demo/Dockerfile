FROM splunk/splunk:8.0.2.1
LABEL authors "Brian Torres-Gil <brian@ixi.us>,Paul Nguyen <panguyen@paloaltonetworks.com>"

# Versions
ENV SPLUNK_USER root
ENV REFRESHED_AT 2020-04-03
ENV APP_VERSION 6.2.0
ENV ADDON_VERSION 6.2.0 
ENV EVENTGEN_VERSION develop

USER root
RUN mkdir /panw-apps

# Download the latest stable Palo Alto Networks App for Splunk

RUN wget -qO /SplunkforPaloAltoNetworks.tar.gz https://github.com/PaloAltoNetworks/SplunkforPaloAltoNetworks/archive/${APP_VERSION}.tar.gz
RUN tar -xzf /SplunkforPaloAltoNetworks.tar.gz -C /panw-apps/
RUN mv /panw-apps/SplunkforPaloAltoNetworks-${APP_VERSION} /panw-apps/SplunkforPaloAltoNetworks
RUN rm -f /SplunkforPaloAltoNetworks.tar.gz
RUN mkdir /panw-apps/SplunkforPaloAltoNetworks/local
COPY conf/datamodels.conf /panw-apps/SplunkforPaloAltoNetworks/local/datamodels.conf
RUN cd /panw-apps; tar czf /panw-apps/SplunkforPaloAltoNetworks.tgz SplunkforPaloAltoNetworks

# Download the latest stable Palo Alto Networks Add-on for Splunk
RUN wget -qO /Splunk_TA_paloalto.tar.gz https://github.com/PaloAltoNetworks/Splunk_TA_paloalto/archive/${ADDON_VERSION}.tar.gz
RUN tar -xzf /Splunk_TA_paloalto.tar.gz -C /panw-apps/
RUN mv /panw-apps/Splunk_TA_paloalto-${ADDON_VERSION} /panw-apps/Splunk_TA_paloalto
RUN rm -f /Splunk_TA_paloalto.tar.gz
RUN mkdir /panw-apps/Splunk_TA_paloalto/local
# Add 514/udp syslog input to app
COPY conf/inputs.conf /panw-apps/Splunk_TA_paloalto/local/inputs.conf
COPY samples /panw-apps/Splunk_TA_paloalto/samples
COPY conf/eventgen_conf/eventgen.conf /panw-apps/Splunk_TA_paloalto/default/eventgen.conf
COPY conf/eventgen_conf/eventgen.conf.spec /panw-apps/Splunk_TA_paloalto/README/eventgen.conf.spec
COPY conf/eventgen_conf/eventgen_kvstore_loader.py /panw-apps/Splunk_TA_paloalto/bin/eventgen_kvstore_loader.py
RUN cd /panw-apps; tar czf /panw-apps/Splunk_TA_paloalto.tgz Splunk_TA_paloalto

# Download the latest stable Eventgen
RUN wget -qO /eventgen.tar.gz https://github.com/btorresgil/eventgen/archive/${EVENTGEN_VERSION}.tar.gz
RUN tar -xzf /eventgen.tar.gz -C /panw-apps/
RUN mv /panw-apps/eventgen-${EVENTGEN_VERSION} /panw-apps/SA-Eventgen
RUN rm -f /eventgen.tar.gz
RUN cd /panw-apps; tar czf /panw-apps/eventgen.tgz SA-Eventgen

# Splunk configuration
ENV SPLUNK_START_ARGS --accept-license
ENV SPLUNK_APPS_URL "/panw-apps/SplunkforPaloAltoNetworks.tgz,/panw-apps/Splunk_TA_paloalto.tgz,/panw-apps/eventgen.tgz"
COPY create_demo_user.yml /tmp/create_demo_user.yml
COPY default.yml /tmp/defaults/default.yml

# Ports Splunk Web, Splunk Daemon, KVStore, Splunk Indexing Port, Network Input, HTTP Event Collector
EXPOSE 8000/tcp 8089/tcp 8191/tcp 9997/tcp 1514 8088/tcp

WORKDIR /opt/splunk

# Configurations folder, var folder for everything (indexes, logs, kvstore)
VOLUME [ "/opt/splunk/etc", "/opt/splunk/var" ]

ENTRYPOINT ["/sbin/entrypoint.sh"]
CMD ["start-service"]
