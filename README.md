<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-green?style=for-the-badge" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Version-1.0.0-red?style=for-the-badge" alt="Version">
</p>

<h1 align="center">🔐 AURA'S BRUTER</h1>

<p align="center">
  <strong>Multi-Protocol Brute Force Security Testing Tool</strong><br>
  <em>SSH • FTP • Telnet</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/⚡-Fast%20Multi--Threading-orange?style=flat-square" alt="Fast">
  <img src="https://img.shields.io/badge/🛡️-Fail2ban%20Bypass-purple?style=flat-square" alt="Bypass">
  <img src="https://img.shields.io/badge/📱-Telegram%20Notifications-blue?style=flat-square" alt="Telegram">
  <img src="https://img.shields.io/badge/💾-Session%20Save%2FResume-green?style=flat-square" alt="Sessions">
</p>

---

## ⚠️ Disclaimer

> **This tool is intended for EDUCATIONAL and AUTHORIZED SECURITY TESTING purposes only.**
> 
> - Only use on systems you **own** or have **explicit permission** to test
> - Unauthorized access to computer systems is **illegal**
> - The author is **not responsible** for any misuse of this tool

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎨 **RGB Animated Banner** | Beautiful rainbow animation on startup |
| 🔐 **Multi-Protocol** | SSH, FTP, and Telnet support |
| 📚 **Dictionary Attack** | Wordlist-based attacks with custom schemas |
| 🔧 **Generation Attack** | Character-based password generation |
| 🧠 **Smart Attack** | Common password patterns |
| ⚡ **Multi-Threading** | Configurable thread pool (1-100) |
| 🛡️ **Rate Limiting** | Adaptive delays + stealth mode |
| 💾 **Session Management** | Save and resume attacks |
| 📱 **Telegram Bot** | Real-time notifications + remote control |
| 💬 **Discord Webhook** | Notification support |
| 🖥️ **Hybrid Interface** | Interactive TUI + CLI arguments |

---

## 🚀 Installation

### Kali Linux / Debian

```bash
git clone https://github.com/YOUR_USERNAME/auras-bruter.git
cd auras-bruter
chmod +x install.sh
./install.sh
```

### Manual Installation

```bash
git clone https://github.com/YOUR_USERNAME/auras-bruter.git
cd auras-bruter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 💻 Usage

### Interactive Mode (TUI)

```bash
python aura_bruter.py
```

### CLI Mode

```bash
# SSH Dictionary Attack
python aura_bruter.py --ssh --dict -H 192.168.1.100 -u users.txt -p passwords.txt

# FTP Generation Attack  
python aura_bruter.py --ftp --gen -H 192.168.1.100 --user admin --lower --digits --max-len 6

# Smart Attack with Stealth Mode
python aura_bruter.py --ssh --smart -H 192.168.1.100 --user root --stealth

# Resume Previous Session
python aura_bruter.py --resume SESSION_ID
```

### CLI Options

```
Protocol:
  --ssh           SSH protocol (port 22)
  --ftp           FTP protocol (port 21)
  --telnet        Telnet protocol (port 23)

Target:
  -H, --host      Target host
  -P, --port      Target port

Attack Mode:
  --dict          Dictionary attack (wordlists)
  --gen           Generation attack (charset)
  --smart         Smart pattern attack

Dictionary Options:
  -u, --users     Username wordlist file
  -p, --passwords Password wordlist file
  -c, --combo     Combo file (user:pass format)

Generation Options:
  --user          Target username
  --lower         Include lowercase (a-z)
  --upper         Include uppercase (A-Z)
  --digits        Include digits (0-9)
  --symbols       Include symbols
  --min-len       Minimum password length
  --max-len       Maximum password length

Performance:
  -t, --threads       Number of threads (default: 10)
  --no-rate-limit     Disable rate limiting
  --stealth           Enable stealth mode (slow, careful)
```

---

## 📱 Telegram Bot

Control your attacks remotely with Telegram bot commands:

| Command | Description |
|---------|-------------|
| `/status` | View current attack progress |
| `/results` | View found credentials |
| `/stop` | Stop current attack |
| `/help` | Show available commands |

### Setup

1. Create a bot with [@BotFather](https://t.me/BotFather)
2. Get your Chat ID from [@userinfobot](https://t.me/userinfobot)
3. Edit `config.json`:

```json
{
  "telegram": {
    "enabled": true,
    "token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  }
}
```

---

## 📁 Project Structure

```
auras-bruter/
├── aura_bruter.py          # Main entry point
├── install.sh              # Kali Linux installer
├── config.json             # Configuration
├── requirements.txt        # Dependencies
│
├── core/
│   ├── attack_engine.py    # Multi-threaded attack engine
│   ├── rate_limiter.py     # Fail2ban bypass
│   ├── session_manager.py  # Save/resume sessions
│   └── notifier.py         # Telegram/Discord
│
├── protocols/
│   ├── ssh_attack.py       # SSH (Paramiko)
│   ├── ftp_attack.py       # FTP
│   └── telnet_attack.py    # Telnet
│
├── attacks/
│   ├── dictionary_attack.py
│   └── generation_attack.py
│
├── ui/
│   ├── banner.py           # RGB animated banner
│   ├── menu.py             # Interactive menus
│   └── display.py          # Progress display
│
├── utils/
│   └── logger.py           # Logging & export
│
└── wordlists/
    ├── common_users.txt
    └── common_passwords.txt
```

---

## ⚙️ Configuration

Edit `config.json` to customize:

```json
{
  "telegram": {
    "enabled": true,
    "token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  },
  "discord": {
    "enabled": false,
    "webhook_url": ""
  },
  "rate_limiting": {
    "enabled": true,
    "base_delay": 0.5,
    "stealth_mode": false
  },
  "attack": {
    "threads": 10,
    "timeout": 10
  }
}
```

---

## 🛡️ Rate Limiting & Stealth

Aura's Bruter includes advanced techniques to avoid detection:

- **Adaptive Delays** - Automatically adjusts timing based on server response
- **Stealth Mode** - 5-15 second delays between attempts
- **Exponential Backoff** - Increases delay after consecutive failures
- **Random Jitter** - Adds ±30% randomness to delays

---

## 📋 Requirements

- Python 3.8+ (tested with 3.8 - 3.13)
- paramiko
- rich
- aiohttp
- python-telegram-bot

---

## 📜 License

This project is licensed under the MIT License.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

<p align="center">
  <strong>Made with ❤️ for educational purposes</strong><br>
  <em>Use responsibly and legally!</em>
</p>
