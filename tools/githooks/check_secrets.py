"""check_secrets.py — run before every commit (tools/githooks/pre-commit). Stops the commit if what's being committed
contains anything that must never be in this public repo: passwords, keys, tokens, connection strings with secrets,
private keys, settings files, data files, or personal contact details.

To check without committing:  python3 tools/githooks/check_secrets.py
"""

import re
import subprocess
import sys

BLOCK_FILES = [r"(^|/)\.env$", r"(^|/)\.env\.(?!example$)", r"database\.env$", r"\.(pem|pfx|p12|key|publishsettings)$",
               r"(^|/)id_(rsa|ed25519)", r"\.csv$", r"credentials", r"\.azure/"]
PATTERNS = {
    "password in a connection string": r"(?i)\b(password|pwd)\s*=\s*[^;\s'\"{}]{4,}",
    "SQL password set in a file": r"(?i)SQL_PASSWORD\s*[:=]\s*['\"]?[^\s'\"{$\[]{4,}",
    "password in a command": r"(?i)(--admin-password|WITH\s+PASSWORD\s*=)\s*['\"]?(?!\[\[)[^\s'\"{$\[)]{4,}",
    "storage / service bus key": r"(?i)(AccountKey|SharedAccessKey|SharedAccessSignature)\s*=",
    "client secret": r"(?i)client[_-]?secret\s*[:=]\s*['\"]?[A-Za-z0-9~._-]{8,}",
    "private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "AWS key": r"AKIA[0-9A-Z]{16}",
    "GitHub token": r"gh[pousr]_[A-Za-z0-9]{30,}",
    "API key": r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{35}",
    "assigned secret": r"(?i)\b(api[_-]?key|secret|token|passwd)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]",
    "personal email": r"[A-Za-z0-9._%+-]+@(gmail|hotmail|outlook|yahoo|icloud|live|bigpond)\.[A-Za-z.]{2,}",
    "mobile number": r"\b04\d{2}[ -]?\d{3}[ -]?\d{3}\b",
}
ALLOW = re.compile(r"\[\[[A-Z_]+\]\]|noreply|example\.com|check_secrets\.py")


def main():
    files = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], capture_output=True, text=True).stdout.split()
    problems = [f"{f}: this kind of file never goes in git" for f in files if any(re.search(p, f) for p in BLOCK_FILES)]
    diff = subprocess.run(["git", "diff", "--cached", "-U0", "--no-color", "--", ".", ":(exclude)media", ":(exclude)*.pdf",
                           ":(exclude)*.xlsx", ":(exclude)*.pptx", ":(exclude)*.png", ":(exclude)*.mp4"], capture_output=True, text=True, errors="replace").stdout
    current = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif line.startswith("+") and not line.startswith("+++") and current and not current.endswith("check_secrets.py"):
            for label, pat in PATTERNS.items():
                m = re.search(pat, line)
                if m and not ALLOW.search(m.group(0)):
                    problems.append(f"{current}: {label}: {line[1:].strip()[:100]}")
    if problems:
        print("COMMIT STOPPED: this would put something private into the public repo:\n  " + "\n  ".join(problems[:20]))
        print("\nRemove it (settings go in OneDrive Config/; the SQL password goes in FOURTH_SHEET_SQL_PASSWORD in your environment, "
              "the git-ignored .env, or Azure Key Vault), then commit again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
