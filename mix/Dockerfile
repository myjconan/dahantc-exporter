# syntax=docker/dockerfile:1

FROM python
RUN mkdir -p /usr/local/5gucp_monitor/exporter/dahantc_exporter/
RUN mkdir -p /root/.kube/
COPY ./app/dahantc_exporter.py /usr/local/5gucp_monitor/exporter/dahantc_exporter/
COPY ./config/*.ini /usr/local/5gucp_monitor/exporter/dahantc_exporter/
COPY prep_dahantc_exporter_env.sh /usr/local/5gucp_monitor/exporter/dahantc_exporter/
COPY ./config/k8s_config.txt /root/.kube/
RUN /usr/bin/sh /usr/local/5gucp_monitor/exporter/dahantc_exporter/prep_dahantc_exporter_env.sh
ENTRYPOINT ["/usr/local/bin/python","/usr/local/5gucp_monitor/exporter/dahantc_exporter/dahantc_exporter.py"]
EXPOSE 80
