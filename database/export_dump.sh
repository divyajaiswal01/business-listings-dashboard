#!/usr/bin/env bash
# Creates the .sql dump required for submission (schema + data).
# Usage: ./database/export_dump.sh [mysql_user]   (default: root)
set -euo pipefail
USER_NAME="${1:-root}"
mysqldump -u "$USER_NAME" -p --single-transaction --routines \
  --databases listings_db > "$(dirname "$0")/listings_dump.sql"
echo "Wrote database/listings_dump.sql"
