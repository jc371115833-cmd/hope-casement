#!/usr/bin/env bash
set -euo pipefail

fail() { echo "$*" >&2; exit 1; }
tag=${GITHUB_REF_NAME:?}
[[ $tag =~ ^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ && $GITHUB_REF == "refs/tags/$tag" ]] || fail "Expected a vX.Y.Z tag push."
commit=$(git rev-parse --verify "${GITHUB_SHA:?}^{commit}")
releases="repos/${GH_REPO:?}/releases"
[[ $(git rev-parse HEAD) == "$commit" ]] || fail "Checkout differs from the tag event."
remote_commit=$(gh api "repos/$GH_REPO/commits/$tag" --jq .sha)
[[ $remote_commit == "$commit" ]] || fail "Remote tag $tag no longer points to $commit."

installer="HopeCasement-Setup-$tag.exe"
assets=("$installer" SHA256SUMS.txt)
dir=release-assets
sha=$(sha256sum "$dir/$installer" | cut -d ' ' -f1)
[[ $(tr -d '\r' < "$dir/SHA256SUMS.txt") == "$sha  $installer" ]] || fail "Checksum does not match $installer."
checksums=("$sha" "$(sha256sum "$dir/SHA256SUMS.txt" | cut -d ' ' -f1)")

notes=$(mktemp)
trap 'rm -f -- "$notes"' EXIT
repo_url="${GITHUB_SERVER_URL:?}/$GH_REPO"
cat "docs/releases/$tag.md" > "$notes"
printf '\n## 构建信息\n\n`%s` 的 SHA-256 为 `%s`。\n\n[源码提交](%s/commit/%s) · [Windows CI 与发布记录](%s/actions/runs/%s)\n' \
    "$installer" "$sha" "$repo_url" "$commit" "$repo_url" "${GITHUB_RUN_ID:?}" >> "$notes"

# Listing includes authenticated drafts and distinguishes absence from a failed API call.
id=$(gh api --paginate "$releases?per_page=100" | jq -sr --arg tag "$tag" '
    [.[][] | select(.tag_name == $tag)] |
    if length > 1 then error("Multiple releases for tag") else .[0].id // empty end')
if [[ -z $id ]]; then
    id=$(gh api --method POST "$releases" -f tag_name="$tag" -f target_commitish="$commit" \
        -f name="HopeCasement $tag" -F draft=true -F "body=@$notes" --jq .id)
fi

read_draft() {
    gh api "$releases/$id" | jq -ce --arg tag "$tag" \
        'if .draft and .tag_name == $tag then . else error("Expected a draft for " + $tag) end'
}
release=$(read_draft)

# Preflight all existing uploads before changing the draft. A zero-byte starter
# is GitHub's placeholder for an interrupted upload.
for i in "${!assets[@]}"; do
    jq -e --arg name "${assets[i]}" --arg digest "sha256:${checksums[i]}" '
        all(.assets[] | select(.name == $name);
            (.state == "uploaded" and .digest == $digest) or (.state == "starter" and .size == 0))
    ' <<< "$release" >/dev/null || fail "Conflicting release asset: ${assets[i]}."
done

for i in "${!assets[@]}"; do
    release=$(read_draft)
    asset=$(jq -c --arg name "${assets[i]}" '.assets[] | select(.name == $name)' <<< "$release")
    if [[ -n $asset ]]; then
        if jq -e --arg digest "sha256:${checksums[i]}" '.state == "uploaded" and .digest == $digest' <<< "$asset" >/dev/null; then
            continue
        fi
        jq -e '.state == "starter" and .size == 0' <<< "$asset" >/dev/null || fail "Conflicting release asset: ${assets[i]}."
        gh api --method DELETE "$releases/assets/$(jq -r .id <<< "$asset")"
    fi
    gh release upload "$tag" "$dir/${assets[i]}" --repo "$GH_REPO"
done

release=$(read_draft)
for i in "${!assets[@]}"; do
    jq -e --arg name "${assets[i]}" --arg digest "sha256:${checksums[i]}" \
        'any(.assets[]; .name == $name and .state == "uploaded" and .digest == $digest)' \
        <<< "$release" >/dev/null || fail "GitHub did not confirm the digest of ${assets[i]}."
done

# Preserve hand-written acceptance notes when reusing a pre-existing draft.
if ! jq -e --rawfile generated "$notes" '(.body // "") | contains($generated | rtrimstr("\n"))' <<< "$release" >/dev/null; then
    body=$(jq -r --rawfile generated "$notes" '[(.body // ""), $generated] | map(select(length > 0)) | join("\n\n")' <<< "$release")
    gh api --method PATCH "$releases/$id" -f body="$body" --silent
fi
url=$(jq -r .html_url <<< "$release")
printf '[%s 草稿 Release](%s)\n\n`%s` SHA-256 `%s`\n' "$tag" "$url" "$installer" "$sha" | tee -a "${GITHUB_STEP_SUMMARY:?}"
