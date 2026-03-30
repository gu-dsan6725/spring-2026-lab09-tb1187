#!/usr/bin/env bash
# Alice - Session 2 (new run_id, cross-session memory recall)

BASE_URL="http://127.0.0.1:9090"
OUTPUT="alice_output.txt"

echo "=== Alice Session 2 (New Session) ===" >> "$OUTPUT"
echo "" >> "$OUTPUT"

send() {
  local label="$1"
  local query="$2"
  echo "User: $label" >> "$OUTPUT"
  response=$(curl -s -X POST "$BASE_URL/invocation" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"alice\", \"run_id\": \"alice-session-2\", \"query\": \"$query\"}" \
    | jq -r '.response')
  echo "Agent: $response" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
}

send "What do you remember about me?" "What do you remember about me?"
send "What project am I working on?" "What project am I working on?"

echo "Done. Output appended to $OUTPUT"
