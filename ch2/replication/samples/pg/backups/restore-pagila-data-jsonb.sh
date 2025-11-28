#!/bin/sh

pg_restore /docker-entrypoint-initdb.d/pagila-data-apt-jsonb.backup -d db

pg_restore /docker-entrypoint-initdb.d/pagila-data-yum-jsonb.backup -d db