
FROM ubuntu:22.04
# Installation de clang (demandé par votre Makefile) et libmicrohttpd
RUN apt-get update && apt-get install -y \
    clang \
    make \
    libmicrohttpd-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Compilation du wrapper web
RUN clang -Wall -o auth_service web_wrapper.c -lmicrohttpd

EXPOSE 8082

# Lancement
CMD ["./auth_service", "8082"]
