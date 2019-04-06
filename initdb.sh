#!/bin/bash

set -eo pipefail

DB_NAME="$1"
LINK_LENGTH="$2"

usage() {
    echo "Usage: $0 <DB_NAME> <LINK_LENGTH>" >&2
    exit 1
}

if [[ -z "$DB_NAME" ]]; then
    usage
fi
if [[ -z "$LINK_LENGTH" ]]; then
    usage
fi

sqlite3 "$DB_NAME" < <( \
    cat schema/sqlite.sql; \
    echo "INSERT INTO markov_metadata VALUES ($LINK_LENGTH);" \
)
