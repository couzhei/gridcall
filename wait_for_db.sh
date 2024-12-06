#!/bin/sh
until nc -z -v -w30 "$CASSANDRA_HOST" "$CASSANDRA_PORT"; do
    echo "Waiting for Cassandra to start..."
    sleep 5
done
echo "Cassandra is up!"
exec "$@"
