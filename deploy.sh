#!/bin/zsh
# Deploy showsourcing.app to Cloudflare Pages (project showsourcing-site).
#   ./deploy.sh          -> production (showsourcing.app)
#   ./deploy.sh preview  -> preview.showsourcing.app (unlinked test copy, noindex)
# Only git-tracked (and new, not ignored) site files go up. CLAUDE.md, deploy.sh, CNAME and .nojekyll stay private.
set -e
cd "${0:A:h}"
# Fresh Help/FAQ + changelog from the app (scripts/build_changelog.py, then copy).
python3 ../scripts/build_changelog.py || echo "changelog not refreshed"
./build_help.sh
BRANCH=main
[[ "$1" == "preview" ]] && BRANCH=preview
STAGE=$(mktemp -d)
git ls-files --cached --others --exclude-standard \
  | grep -v -e '^CNAME$' -e '^\.nojekyll$' -e '^CLAUDE\.md$' -e '^deploy\.sh$' \
  | rsync -a --files-from=- . "$STAGE/"
if [[ $BRANCH == preview ]]; then
  # Keep the test copy out of search engines.
  find "$STAGE" -name "*.html" -exec perl -0pi -e 's|<head>|<head>\n<meta name="robots" content="noindex, nofollow">|' {} \;
  printf '\n/*\n  X-Robots-Tag: noindex, nofollow\n' >> "$STAGE/_headers"
  printf 'User-agent: *\nDisallow: /\n' > "$STAGE/robots.txt"
fi
cd "$STAGE"
CLOUDFLARE_API_TOKEN=$(security find-generic-password -s cloudflare_api_token -w) \
CLOUDFLARE_ACCOUNT_ID=28b22d2560f6428a26cd8220fc5a4393 \
  npx -y wrangler pages deploy . --project-name showsourcing-site --branch $BRANCH --commit-dirty=true
