FROM baserow/baserow:latest

COPY . /baserow/

# Установка всех зависимостей и сборка
RUN /baserow/supervisor/docker/docker-entrypoint.sh install-dependencies

# Очистка кэша и временных файлов
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
