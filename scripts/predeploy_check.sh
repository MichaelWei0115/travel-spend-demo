#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

PASS=0
FAIL=0

ok() { echo "  ✅ $1"; PASS=$((PASS+1)); }
fail() { echo "  ❌ $1"; FAIL=$((FAIL+1)); }

echo "================================================"
echo "  Pre-deploy Check — Streamlit Community Cloud"
echo "================================================"

# 1. Python version
echo ""
echo "== Python version =="
python3 --version && ok "Python available" || fail "Python3 not found"

# 2. Requirements
echo ""
echo "== Requirements install check =="
if python3 -m pip install -r requirements.txt -q 2>/dev/null; then
  ok "requirements.txt installs cleanly"
else
  fail "requirements.txt install failed"
fi

# 3. Import checks
echo ""
echo "== Import checks =="
python3 -c "import auth_gate; print('auth_gate ok')" 2>/dev/null && ok "auth_gate import" || fail "auth_gate import"
python3 -c "from pathlib import Path; print('pathlib ok')" && ok "pathlib import" || fail "pathlib import"

# 4. Streamlit config — no local-only bindings
echo ""
echo "== Streamlit config check =="
if rg -qn "127\.0\.0\.1|localhost|serverAddress|address\s*=" .streamlit/config.toml 2>/dev/null; then
  fail "Found local-only config in .streamlit/config.toml"
else
  ok "No local-only bindings in .streamlit/config.toml"
fi

# 5. No local absolute path leaks
echo ""
echo "== Local absolute path leak check =="
if rg -qn "/Users/|/home/|C:\\\\" --glob '*.py' --glob '!scripts/*' . 2>/dev/null | grep -v __pycache__ | grep -v '.bak' | grep -v '.pre_'; then
  fail "Found possible local absolute path references (see above)"
else
  ok "No local absolute path leaks in .py files"
fi

# 6. Secret leak check
echo ""
echo "== Secret leak check =="
if git ls-files | grep -qE '(^|/)\.streamlit/secrets\.toml$'; then
  fail ".streamlit/secrets.toml is tracked by git — remove before deploy"
else
  ok ".streamlit/secrets.toml not tracked by git"
fi

# 7. Required deploy files exist
echo ""
echo "== Required deploy files =="
for f in requirements.txt packages.txt .streamlit/config.toml .streamlit/secrets.toml.example DEPLOYMENT.md app.py auth_gate.py; do
  if [ -f "$f" ]; then
    ok "$f exists"
  else
    fail "$f missing"
  fi
done

# 8. Data and assets tracked
echo ""
echo "== Data and assets tracked check =="
if git ls-files data | grep -q .; then
  ok "data/ files tracked in git"
else
  fail "No tracked files under data/"
fi

if git ls-files assets | grep -q .; then
  ok "assets/ files tracked in git"
else
  fail "No tracked files under assets/"
fi

# 9. Tests
echo ""
echo "== Tests =="
if python3 -m pytest tests/ -q --tb=short 2>/dev/null; then
  ok "pytest passed"
else
  fail "pytest failed (may need streamlit runtime — non-blocking for deploy)"
fi

# 10. Git remote
echo ""
echo "== Git remote =="
if git remote -v 2>/dev/null | grep -q origin; then
  ok "Git remote 'origin' configured"
  git remote -v
else
  fail "No git remote 'origin' configured — needed for Streamlit Cloud deploy"
fi

# 11. Git status
echo ""
echo "== Git status =="
git status --short

# Summary
echo ""
echo "================================================"
echo "  Results: $PASS passed, $FAIL failed"
echo "================================================"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
