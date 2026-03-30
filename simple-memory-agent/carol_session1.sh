#!/usr/bin/env bash
# Carol - Session 1 (user isolation demo)

BASE_URL="http://127.0.0.1:9090"
OUTPUT="carol_output.txt"

echo "=== Carol Session 1 ===" > "$OUTPUT"
echo "" >> "$OUTPUT"

send() {
  local label="$1"
  local query="$2"
  echo "User: $label" >> "$OUTPUT"
  response=$(curl -s -X POST "$BASE_URL/invocation" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"carol\", \"run_id\": \"carol-session-1\", \"query\": \"$query\"}" \
    | jq -r '.response')
  echo "Agent: $response" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
}

send "Hi, I'm Carol. I'm a data scientist." "Hi, I'm Carol. I'm a data scientist."
send "What programming languages do I like?" "What programming languages do I like?"
send "Do you know what Alice prefers?" "Do you know what Alice prefers?"

echo "Done. Output written to $OUTPUT"
