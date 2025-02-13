#!/bin/bash

# Запускаем все необходимые сервисы
exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
