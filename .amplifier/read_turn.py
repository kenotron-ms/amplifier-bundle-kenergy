import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    raw = f.read()

decoder = json.JSONDecoder()
objs = []
idx = 0
n = len(raw)
while idx < n:
    brace = raw.find("{", idx)
    if brace == -1:
        break
    try:
        d, end = decoder.raw_decode(raw, brace)
        objs.append(d)
        idx = end
    except json.JSONDecodeError:
        idx = brace + 1

print(f"FOUND {len(objs)} JSON OBJECT(S)")
for i, d in enumerate(objs):
    print(f"--- OBJECT {i} ---")
    print("session_id:", d.get("session_id"))
    print("timestamp:", d.get("timestamp"))
    resp = str(d.get("response", ""))
    print("response_len:", len(resp))
    print("last 500 chars:", resp[-500:])
