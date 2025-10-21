FROM b4bz/homer:latest

COPY config.yml  /www/assets/config.yml
COPY icons/.     /www/assets/icons/

EXPOSE 8080 

WORKDIR /www

ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]
