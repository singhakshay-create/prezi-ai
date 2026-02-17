#!/bin/bash
# Convenience wrapper - calls start-local.sh
exec "$(dirname "$0")/start-local.sh" "$@"
