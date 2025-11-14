#!/bin/bash
# Convenience wrapper for testing
if [ "$1" = "migration" ]; then
    ./scripts/testing/test-migration.sh
else
    npm test
fi
