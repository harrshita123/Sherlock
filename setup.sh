#!/usr/bin/env bash
set -euo pipefail

echo "Starting setup..."

# Ensure permissions
chmod +x cli.sh web.sh grade.sh grader.sh grader/*.sh 2>/dev/null || true

# Decompress block fixtures
if ls fixtures/*.gz 1> /dev/null 2>&1; then
    for f in fixtures/*.gz; do
        echo "Decompressing $f..."
        gunzip -kf "$f" || echo "Warning: failed to decompress $f"
    done
else
    echo "No .gz fixtures found, skipping decompression."
fi

echo "Setup complete"
