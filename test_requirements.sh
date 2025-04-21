#!/bin/bash
# Validate requirements processing
set -euo pipefail

# Debug: Show environment
echo "=== Current Directory ==="
pwd
ls -la

echo "\n=== Original requirements.txt ==="
cat requirements.txt

# Filter valid packages
echo "\n=== Processing requirements.txt ==="
grep -vE '^(#|$|imaplib|email|argparse|sys|os|logging)' requirements.txt > valid_requirements.txt || {
    echo "⚠️ Warning: No packages matched filter"
    touch valid_requirements.txt
}

echo "\n=== Filtered Packages ==="
cat valid_requirements.txt

# Validate
if [ ! -s valid_requirements.txt ]; then
    echo "::error::No valid packages found in requirements.txt"
    exit 1
else
    echo "✅ Valid packages detected"
    echo "\n=== Verifying installability ==="
    pip check -r valid_requirements.txt
fi

exit 0 