#!/bin/zsh
# Copy the app's Help files into the site, so the app and /help show the same text.
# Run after scripts/build_changelog.py, before ./deploy.sh.
set -e
cd "${0:A:h}"
SRC="../Show Sourcing/Resources/Help"
cp "$SRC/help.json" "$SRC/changelog.json" help/
echo "Copied help.json and changelog.json into Website/help/"
python3 build_pages.py
