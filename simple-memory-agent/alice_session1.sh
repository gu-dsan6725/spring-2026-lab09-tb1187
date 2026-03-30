#!/usr/bin/env bash
# Alice - Session 1 (5 turns, same run_id)

BASE_URL="http://127.0.0.1:9090"
OUTPUT="alice_output.txt"

echo "=== Alice Session 1 ===" > "$OUTPUT"
echo "" >> "$OUTPUT"

send() {
  local label="$1"
  local query="$2"
  echo "User: $label" >> "$OUTPUT"
  response=$(curl -s -X POST "$BASE_URL/invocation" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"alice\", \"run_id\": \"alice-session-1\", \"query\": \"$query\"}" \
    | jq -r '.response')
  echo "Agent: $response" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
}

send "Hi, I'm Alice. I'm a software engineer." "Hi, I'm Alice. I'm a software engineer."
send "I prefer Python for development." "I prefer Python for development."
send "What programming languages do I like?" "What programming languages do I like?"
send "I'm working on a FastAPI project." "I'm working on a FastAPI project."
send "What have we discussed so far?" "What have we discussed so far?"

echo "Done. Output written to $OUTPUT"
