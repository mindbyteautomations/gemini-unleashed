#!/usr/bin/env bash
# Activate gcloud/gsutil/bq from a service account key.
#
# The key itself is never stored in git. This script reads .env for a pointer
# to it, validates the file, activates it, and verifies the result.
#
#   usage: scripts/gcp-auth.sh [path/to/key.json]

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$REPO/.env" ]]; then
  set -a; . "$REPO/.env"; set +a
fi

# Explicit argument wins, then .env, then the known drop locations.
CANDIDATES=()
# Deliberately no in-repo location: the key lives outside the working tree so
# that no gitignore rule, and no tool that ignores gitignore, stands between
# the key and a public remote.
for c in \
  "${1:-}" \
  "${GOOGLE_APPLICATION_CREDENTIALS:-}" \
  "/root/.claude/gcp/sa-key.json"
do
  [[ -z "$c" ]] && continue
  for seen in ${CANDIDATES[@]+"${CANDIDATES[@]}"}; do
    [[ "$seen" == "$c" ]] && continue 2
  done
  CANDIDATES+=("$c")
done

KEY=""
for c in "${CANDIDATES[@]}"; do
  if [[ -n "$c" && -f "$c" ]]; then KEY="$c"; break; fi
done

if [[ -z "$KEY" ]]; then
  echo "no service account key found. looked in:" >&2
  for c in "${CANDIDATES[@]}"; do [[ -n "$c" ]] && echo "  $c" >&2; done
  exit 1
fi

# Validate before handing it to gcloud, so a truncated or wrong-type file
# fails here with a clear message instead of a generic auth error.
for field in type client_email project_id private_key; do
  if ! jq -e "has(\"$field\")" "$KEY" >/dev/null 2>&1; then
    echo "$KEY is not a valid service account key (missing '$field')" >&2
    exit 1
  fi
done

if [[ "$(jq -r .type "$KEY")" != "service_account" ]]; then
  echo "$KEY has type '$(jq -r .type "$KEY")', expected 'service_account'" >&2
  exit 1
fi

chmod 600 "$KEY"

# CLOUDSDK_AUTH_ACCESS_TOKEN overrides the credential store entirely, and
# gcloud auth print-access-token just echoes it back - so leaving it set
# would both break real API calls and make the check below pass regardless.
if [[ -n "${CLOUDSDK_AUTH_ACCESS_TOKEN:-}" ]]; then
  echo "note: unsetting CLOUDSDK_AUTH_ACCESS_TOKEN, which would override this key"
  unset CLOUDSDK_AUTH_ACCESS_TOKEN
fi

SA="$(jq -r .client_email "$KEY")"
PROJECT="${GOOGLE_CLOUD_PROJECT:-$(jq -r .project_id "$KEY")}"

echo "activating $SA on $PROJECT"
gcloud auth activate-service-account --key-file="$KEY" --quiet
gcloud config set project "$PROJECT" --quiet

# gsutil and bq read ADC rather than the gcloud credential store.
export GOOGLE_APPLICATION_CREDENTIALS="$KEY"

echo
echo "active account: $(gcloud config get-value account 2>/dev/null)"
echo "active project: $(gcloud config get-value project 2>/dev/null)"
echo
if gcloud auth print-access-token >/dev/null 2>&1; then
  echo "token fetch OK - credentials are live"
else
  echo "token fetch FAILED - key activated but cannot mint a token" >&2
  exit 1
fi

# The unset above applied to this script's shell only. If the variable is set
# in the container environment it will be back in the next shell, overriding
# the credential just activated.
if env | grep -q '^CLOUDSDK_AUTH_ACCESS_TOKEN='; then
  echo
  echo "warning: CLOUDSDK_AUTH_ACCESS_TOKEN is set in the environment." >&2
  echo "It overrides this credential in every new shell. Unset it there," >&2
  echo "or prefix gcloud calls with 'env -u CLOUDSDK_AUTH_ACCESS_TOKEN'." >&2
fi
