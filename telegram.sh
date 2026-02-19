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

echo "Using BOT_TOKEN: $BOT_TOKEN"
echo "Using CHAT_ID: $CHAT_ID"
echo "Using PROXY_FILE: $PROXY_FILE"
echo "Max buttons per message: $MAX_BUTTONS_PER_MESSAGE"
echo "Buttons per row: ${BUTTONS_PER_ROW:-5}"

echo "$PROXY_FILE" | od -c

# Check if proxy file exists
if [ ! -f "$PROXY_FILE" ]; then
    echo "Error: Proxy file '$PROXY_FILE' not found!"
    exit 1
fi

# Set default buttons per row if not specified
BUTTONS_PER_ROW=${BUTTONS_PER_ROW:-2}

# Read all proxies into an array
proxies=()
while IFS= read -r line; do
    # Skip empty lines and comments
    if [[ -z "$line" ]] || [[ "$line" =~ ^#.* ]]; then
        continue
    fi

    # Check if line is a valid proxy URL
    if [[ "$line" =~ ^https://t.me/proxy\? ]]; then
        proxies+=("$line")
    fi
done < "$PROXY_FILE"

total_proxies=${#proxies[@]}
echo "Found $total_proxies proxies in file"

if [ $total_proxies -eq 0 ]; then
    echo "Error: No valid proxies found in file!"
    exit 1
fi

# Function to send a batch of proxies
send_proxy_batch() {
    local start_idx=$1
    local end_idx=$2
    local batch_num=$3
    local total_batches=$4

    INLINE_KEYBOARD="["
    local current_row="["
    local buttons_in_row=0

    for ((i=start_idx; i<end_idx && i<total_proxies; i++)); do
        # Add button to current row
        if [ $buttons_in_row -gt 0 ]; then
            current_row+=","
        fi
        current_row+="{\"text\": \"Proxy $((i+1))\", \"url\": \"${proxies[$i]}\"}"
        ((buttons_in_row++))

        # Check if we need to start a new row
        if [ $buttons_in_row -eq $BUTTONS_PER_ROW ] || [ $((i+1)) -eq $end_idx ] || [ $((i+1)) -eq $total_proxies ]; then
            # Close current row
            current_row+="]"

            # Add row to keyboard
            if [ $i -ne $start_idx ] || [ $buttons_in_row -ne 1 ] && [ $i -ne $start_idx ]; then
                if [ "$INLINE_KEYBOARD" != "[" ]; then
                    INLINE_KEYBOARD+=","
                fi
            else
                if [ "$INLINE_KEYBOARD" != "[" ]; then
                    INLINE_KEYBOARD+=","
                fi
            fi

            INLINE_KEYBOARD+="$current_row"

            # Reset for next row
            current_row="["
            buttons_in_row=0
        fi
    done

    INLINE_KEYBOARD+="]"

    # Determine message text
    if [ $total_batches -eq 1 ]; then
        MESSAGE_TEXT="🔐 Choose a Proxy (Total: $total_proxies available)"
    else
        MESSAGE_TEXT="🔐 Proxies (Part $batch_num/$total_batches - Total: $total_proxies available)"
    fi

    # Build JSON payload
    JSON_PAYLOAD=$(cat <<EOF
{
  "chat_id": "$CHAT_ID",
  "text": "$MESSAGE_TEXT",
  "reply_markup": {
    "inline_keyboard": $INLINE_KEYBOARD
  }
}
EOF
)

    # Send message
    echo "Sending batch $batch_num/$total_batches (proxies $((start_idx+1)) to $((end_idx<total_proxies ? end_idx : total_proxies)))..."

    response=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
      -H "Content-Type: application/json" \
      -d "$JSON_PAYLOAD")

    if echo "$response" | grep -q '"ok":true'; then
        echo "  ✓ Batch $batch_num sent successfully!"
    else
        echo "  ✗ Failed to send batch $batch_num!"
        echo "  Response: $response"
        return 1
    fi

    # Small delay to avoid rate limiting
    sleep 0.5
}

# Calculate number of batches needed
total_batches=$(( (total_proxies + MAX_BUTTONS_PER_MESSAGE - 1) / MAX_BUTTONS_PER_MESSAGE ))

echo "Will send $total_batches message(s)"
echo "----------------------------------------"

# Send batches
batch_num=1
for ((start=0; start<total_proxies; start+=MAX_BUTTONS_PER_MESSAGE)); do
    end=$((start + MAX_BUTTONS_PER_MESSAGE))
    send_proxy_batch $start $end $batch_num $total_batches
    ((batch_num++))
done

echo "----------------------------------------"
echo "✓ All messages sent successfully!"