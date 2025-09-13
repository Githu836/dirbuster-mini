# 🔎 dirbuster-mini

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)  
![Python](https://img.shields.io/badge/Python-3.x-blue.svg)  
![Platform](https://img.shields.io/badge/Platform-Termux%20|%20Linux%20|%20Windows-lightgrey.svg)  
![Status](https://img.shields.io/badge/Status-Beta-orange.svg)

**DirBuster Mini** — minimalist incremental directory brute-forcer.  
Lightweight, threaded, and easy to use on Termux / Linux / Windows.

> ⚠️ **IMPORTANT:** Only use this tool on systems you own or have explicit permission to test.

---

## 🔧 What’s included
- `dirbuster-mini.py` — main script (Python 3)
- `requirements.txt` — dependencies
- `common.txt` — sample/common wordlist (put in `wordlists/common.txt` or pass custom path)

---

## ## Installation & Usage

> Format: **one platform = one `##` section** — clear & professional.

## 🔹 Termux (Android)
```bash
pkg update -y
pkg install python -y
pkg install git -y
# clone repo
git clone https://github.com/Githu836/dirbuster-mini.git
cd dirbuster-mini
# install deps
pip install -r requirements.txt
```
## run (example)
python3 dirbuster-mini.py http://example.com -w common.txt -t 20 -d 0.1 -o results.txt
```
##🔹 Linux (Ubuntu / Kali / Debian / Arch)

sudo apt update && sudo apt install python3 python3-pip git -y
git clone https://github.com/Githu836/dirbuster-mini.git
cd dirbuster-mini
pip3 install -r requirements.txt
python3 dirbuster-mini.py
```
## run (example
http://example.com -w common.txt -t 20 -d 0.1 -o results.txt
``
## 🔹 Windows (CMD / PowerShell)

1. Install Python 3.x from https://www.python.org/downloads/


2. Install Git from https://git-scm.com/downloads


3. In PowerShell / CMD:

 ##🔹And

git clone https://github.com/Githu836/dirbuster-mini.git
cd dirbuster-mini
pip install -r requirements.txt
python dirbuster-mini.py 
```

## run (example(
http://example.com -w common.txt -t 20 -d 0.1 -o results.txt
```

---

## 🧭 Usage & Options

usage: dirbuster-mini.py target [-w WORDLIST] [-t THREADS] [-d DELAY] [-o OUTPUT] [-v]

Positional:
  target                Target URL (e.g., http://example.com)

Options:
  -w, --wordlist        Path to wordlist file (default: wordlists/common.txt)
  -t, --threads         Number of threads (default: 10)
  -d, --delay           Delay between requests in seconds (default: 0)
  -o, --output          Output file to save results
  -v, --verbose         Verbose output

Example:

# Quick scan using bundled wordlist
python3 dirbuster-mini.py http://target.local -w common.txt

# Faster, with more threads and small delay
python3 dirbuster-mini.py http://target.local -w common.txt -t 50 -d 0.05 -o found.txt

# Use full path to a wordlist folder
python3 dirbuster-mini.py target.com -w wordlists/common.txt -t 30

```
---

# 🧩 How it works (brief)

Loads your wordlist (single words).

Generates incremental paths (single and word1/word2 combos; depth=2 by default).

Multi-threaded requests; sets simple User-Agent.

Prints colored status codes and saves results if -o specified.


```
---

## 📝 Notes & Tips

For big wordlists don’t set extremely high thread counts on slow devices. Start with -t 20 and tune.

Put your common.txt under wordlists/common.txt OR pass custom path with -w.

If target blocks by User-Agent or WAF, try adjusting headers in the script (requests.Session headers).


```
---

# 📎 Requirements

Add these to requirements.txt:

requests
colorama

Install with pip install -r requirements.txt.

```
---

# 💡 Contributing

PRs welcome ✅ — but keep changes focused:

README improvements, CLI flags, fix bugs, performance tweaks.

If adding heavy features (e.g., recursive crawling), open an issue first.


When contributing:

1. Fork → branch → commit → PR.


2. Use clear commit messages and update README usage when adding flags.

```


---
#🧾 License


This project is licensed under the MIT License — see LICENSE file.
