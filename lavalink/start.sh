#!/bin/sh
./replace_vars.sh ./application.yml
java -Djdk.tls.client.protocols=TLSv1.1,TLSv1.2 -jar Lavalink.jar
