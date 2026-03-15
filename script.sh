#!/bin/bash

# Load environment variables from .env
if [ -f ".env" ]; then
    source .env
else
    echo "Error: .env file not found!"
    exit 1
fi

# Check required variables
if [ -z "$BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
    echo "Error: BOT_TOKEN or CHAT_ID is not set in .env!"
    exit 1
fi

echo "Using BOT_TOKEN: [hidden]"
echo "Using CHAT_ID: $CHAT_ID"

# ── Accept URLs from a file or as arguments ──────────────────────────────────
urls=()

if [ $# -gt 0 ]; then
    urls=("$@")
elif [ -n "$URL_FILES" ]; then
    normalized="$URL_FILES"
    normalized="${normalized#[}"
    normalized="${normalized%]}"
    normalized="${normalized//,/ }"
    normalized="${normalized//\"/}"
    for u in $normalized; do
        [ -z "$u" ] && continue
        urls+=("$u")
    done
fi

total_urls=${#urls[@]}
echo "Found $total_urls URL(s) to process"
echo "----------------------------------------"

if [ $total_urls -eq 0 ]; then
    echo "Error: No URLs to process!"
    echo "Provide URLs as arguments or set URL_FILES in .env"
    exit 1
fi

# ── Temp directory for downloads ─────────────────────────────────────────────
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# ── Helper: send a document to Telegram ──────────────────────────────────────
send_file() {
    local filepath="$1"
    local caption="$2"

    echo "  Sending: $(basename "$filepath") ..."

    # FIX: Use --form-string for text fields so special chars (newlines, emoji)
    #      don't corrupt the multipart body. Use -F only for the file upload.
    response=$(curl -s \
        -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendDocument" \
        -F "document=@${filepath}" \
        --form-string "chat_id=${CHAT_ID}" \
        --form-string "caption=${caption}")

    if echo "$response" | grep -q '"ok":true'; then
        echo "  ✓ Sent successfully!"
    else
        echo "  ✗ Failed to send!"
        echo "  Response: $response"
        return 1
    fi

    sleep 0.5
}

# ── Helper: send plain text ───────────────────────────────────────────────────
send_text_message() {
    local text="$1"

    if [ ${#text} -gt 4096 ]; then
        text="${text:0:4060}"$'\n\n'"... _(truncated)_"
    fi

    response=$(curl -s \
        -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\": \"${CHAT_ID}\", \"text\": $(printf '%s' "$text" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}")

    if echo "$response" | grep -q '"ok":true'; then
        echo "  ✓ Text message sent!"
    else
        echo "  ✗ Failed to send text message!"
        echo "  Response: $response"
        return 1
    fi
}

# ── Process each URL ──────────────────────────────────────────────────────────
success=0
failed=0

for url in "${urls[@]}"; do
    echo ""
    echo "Processing: $url"

    filename=$(basename "$url" | sed 's/[?#].*//')
    [ -z "$filename" ] && filename="file_${success}.txt"
    filepath="${TMP_DIR}/${filename}"

    http_code=$(curl -s -o "$filepath" -w "%{http_code}" -L "$url")

    if [ "$http_code" != "200" ]; then
        echo "  ✗ Download failed! HTTP $http_code — skipping."
        ((failed++))
        continue
    fi

    filesize=$(wc -c < "$filepath")
    echo "  ✓ Downloaded ($filesize bytes)"

    caption="📄 ${filename}
🔗 ${url}"

    # FIX: Check return value — only count as success if send_file succeeded
    if send_file "$filepath" "$caption"; then
        ((success++))
    else
        ((failed++))
        continue
    fi

    if [ "$SEND_INLINE_TEXT" = "true" ] && [ "$filesize" -lt 3000 ]; then
        echo "  Sending content inline..."
        content=$(<"$filepath")
        send_text_message "$content"
    fi
done

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo "✓ Sent:   $success file(s)"
[ $failed -gt 0 ] && echo "✗ Failed: $failed file(s)"
echo "========================================"