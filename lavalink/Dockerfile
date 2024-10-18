FROM fredboat/lavalink:4-alpine
COPY ./application.yml /opt/Lavalink
COPY ./replace_vars.sh /opt/Lavalink
COPY ./start.sh /opt/Lavalink
USER root
RUN apk add --no-cache bash
RUN chmod +x /opt/Lavalink/replace_vars.sh
RUN chmod +x /opt/Lavalink/start.sh
USER lavalink
WORKDIR /opt/Lavalink
ENTRYPOINT ["./start.sh"]
