#!/bin/bash
# Validate requirements processing (Mac-compatible)
set -euo pipefail

echo "=== Current Directory ==="
pwd
ls -la

echo -e "\n=== Original requirements.txt ==="
cat requirements.txt

# Filter valid packages
echo -e "\n=== Processing requirements.txt ==="
grep -vE '^(#|$|imaplib|email|argparse|sys|os|logging)' requirements.txt > valid_requirements.txt || {
    echo "⚠️ No packages matched filter (or file missing)"
    touch valid_requirements.txt
}

echo -e "\n=== Filtered Packages ==="
cat valid_requirements.txt

if [ ! -s valid_requirements.txt ]; then
    echo "::error::No valid packages found"
    exit 1
else
    echo "✅ Valid packages detected"
    echo -e "\n=== Dry Run Installation ==="
    pip install --dry-run -r valid_requirements.txt || {
        echo "::error::Dry run failed"
        exit 1
    }
fi

# Cleanup
rm -f valid_requirements.txt
exit 0 