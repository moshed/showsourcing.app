#!/bin/zsh
# Deploy showsourcing.app to Cloudflare Pages (project showsourcing-site).
# Only git-tracked site files go up. CLAUDE.md, deploy.sh, CNAME and .nojekyll stay private.
set -e
cd "${0:A:h}"
STAGE=$(mktemp -d)
git ls-files --cached --others --exclude-standard \
  | grep -v -e '^CNAME$' -e '^\.nojekyll$' -e '^CLAUDE\.md$' -e '^deploy\.sh$' \
  | rsync -a --files-from=- . "$STAGE/"
cd "$STAGE"
CLOUDFLARE_API_TOKEN=$(security find-generic-password -s cloudflare_api_token -w) \
CLOUDFLARE_ACCOUNT_ID=28b22d2560f6428a26cd8220fc5a4393 \
  npx wrangler pages deploy . --project-name showsourcing-site --branch main --commit-dirty=true
