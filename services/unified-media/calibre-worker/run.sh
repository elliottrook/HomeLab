#!/bin/sh
set -eu

: "${UNIFIED_CALIBRE_LIBRARY_PATH:?UNIFIED_CALIBRE_LIBRARY_PATH is required}"
: "${UNIFIED_BOOK_INGEST_PATH:?UNIFIED_BOOK_INGEST_PATH is required}"
: "${UNIFIED_BOOK_OUTPUT_PATH:?UNIFIED_BOOK_OUTPUT_PATH is required}"

case "${UNIFIED_CALIBRE_LIBRARY_PATH}" in
  /mnt/Media/media/books|/mnt/Media/media/books/*)
    if [ "${ALLOW_PRODUCTION_CALIBRE_WRITE:-}" != "YES" ]; then
      echo "Refusing live Calibre library without ALLOW_PRODUCTION_CALIBRE_WRITE=YES" >&2
      exit 2
    fi
    ;;
esac

action=${1:-}
case "$action" in
  import)
    shift
    [ "$#" -gt 0 ] || { echo "usage: $0 import FILE..." >&2; exit 2; }
    exec calibredb add --with-library /library "$@"
    ;;
  convert)
    shift
    [ "$#" -eq 2 ] || { echo "usage: $0 convert INPUT OUTPUT" >&2; exit 2; }
    exec ebook-convert "$1" "$2"
    ;;
  list)
    exec calibredb --with-library /library list --for-machine
    ;;
  *)
    echo "usage: $0 {import|convert|list} ..." >&2
    exit 2
    ;;
esac
