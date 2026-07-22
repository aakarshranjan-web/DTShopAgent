#!/usr/bin/env bash
# Regression harness: fabricates a complete student environment and runs
# pack_evidence.py through happy path + three violation paths.
# Run from repo root:  bash tests/simulate_submission.sh
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PACK="$REPO/tools/pack_evidence.py"
PASS=0; FAIL=0
check(){ if [ "$1" = "$2" ]; then echo "  PASS: $3"; PASS=$((PASS+1));
         else echo "  FAIL: $3 (got $1, want $2)"; FAIL=$((FAIL+1)); fi; }

mkenv(){
rm -rf ~/dtlab ~/.hermes
mkdir -p ~/dtlab/workspace ~/dtlab/evidence ~/dtlab/human ~/.hermes/sessions
cd ~/dtlab/workspace
printf "student_id,item_code,construct,question,answer,constraint\nDT2026-999,D01,Demo,Age?,26-35,0\n" > persona_survey.csv
echo "# p" > persona_survey.md
printf "# Purchase profile (agent-extracted)\n- top categories: x\n" > purchase_profile.md
printf "## Task 1\nfilled\n" > tasks.md
printf "log citing D01 and PP; candidates search#1..4\n" > decision_log.md
printf "task_id,title,asin,price_inr,sponsored\n1,A,B07GYLZ1ZN,299,0\n2,B,B08YRWN3RD,1299,1\n3,C,B00R9QLRRO,1450,0\n" > agent_picks.csv
printf "# c\n## Task 1\nVerdict: identical\nt\n## Task 2\nVerdict: inferior\nt\n## Task 3\nVerdict: better\nt\n" > comparison.md
printf '{"type":"product_view","asin":"B07GYLZ1ZN"}\n{"type":"product_view","asin":"B09YLFGBLL"}\n{"type":"product_view","asin":"B07D75V2GH"}\n' > ~/dtlab/human/human_session.jsonl
printf "task_id,title,asin,url,price_inr,reasoning\n1,A,B07GYLZ1ZN,u,299,r\n2,S,B09YLFGBLL,u,1490,r\n3,K,B07D75V2GH,u,780,r\n" > ~/dtlab/human/human_picks.csv
echo H_FIRST > ~/dtlab/arm.txt
sleep 0.2; touch ~/dtlab/.run_started; sleep 0.1
echo '{"t":1}' > ~/.hermes/sessions/s.jsonl
python3 - <<'PY'
import zlib,struct,os
def c(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d))
raw=b''.join(b'\x00'+b'\xf0'*600 for _ in range(100))
png=b'\x89PNG\r\n\x1a\n'+c(b'IHDR',struct.pack('>IIBBBBB',200,100,8,2,0,0,0))+c(b'IDAT',zlib.compress(raw))+c(b'IEND',b'')
open(os.path.expanduser('~/dtlab/evidence/cart.png'),'wb').write(png)
PY
}

echo "[1] happy path (H_FIRST)"
mkenv; python3 "$PACK" >/dev/null 2>&1; check $? 0 "valid pack exits 0"

echo "[2] verdict/ASIN cross-check"
mkenv; sed -i 's/Verdict: identical/Verdict: equivalent/' ~/dtlab/workspace/comparison.md
python3 "$PACK" 2>&1 | grep -q "must be 'identical'"; check $? 0 "same-ASIN wrong verdict caught"

echo "[3] bias quarantine"
mkenv; cp ~/dtlab/human/human_picks.csv ~/dtlab/workspace/
python3 "$PACK" 2>&1 | grep -q "quarantine violated"; check $? 0 "leak into agent workspace caught"

echo "[4] A_FIRST ordering violation (backdated human session)"
mkenv; echo A_FIRST > ~/dtlab/arm.txt
python3 - <<'PY'
import os,time
t=time.time()-7200
os.utime(os.path.expanduser('~/dtlab/human/human_session.jsonl'),(t,t))
PY
python3 "$PACK" 2>&1 | grep -q "A_FIRST arm: human session predates"; check $? 0 "reverse-order violation caught"

rm -rf ~/dtlab ~/.hermes
echo ""; echo "Results: $PASS passed, $FAIL failed"
exit $FAIL
