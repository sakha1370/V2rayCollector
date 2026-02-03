# 🛰️ V2rayCollector
<p align="center">
  <img src="https://img.shields.io/badge/Status-Active-success?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/github/go-mod/go-version/mrvcoder/V2rayCollector?style=for-the-badge" alt="Go Version">
  <img src="https://img.shields.io/github/license/mrvcoder/V2rayCollector?style=for-the-badge" alt="License">
</p>

<p align="center">
  <strong>Free, automated, and reliable V2Ray proxy lists for everyone</strong>
</p>

<p align="center">
  🚀 <a href="#-quick-start">Quick Start</a> • 📋 <a href="#-proxy-collections">Proxy Lists</a> • 🤝 <a href="#-contributing">Contributing</a>
</p>

---

## ✨ Features

- **🔍 Smart Discovery**: Periodically scrapes hundreds of Telegram channels for the latest proxy configurations.
- **⚡ Multi-Protocol Support**: Full support for `VMess`, `VLess`, `Trojan`, `Shadowsocks (SS)`, `MTProto`, `HTTP`, and `SOCKS` proxies.
- **🧹 Intelligent Filtering**: Automatically identifies and extracts valid configs using optimized regular expressions.
- **📦 Organized Collections**: Categorizes proxies into dedicated protocol-specific files.
- **📊 Metadata Extraction**: Saves detailed proxy metadata in `proxies_metadata.json` for analysis.
- **⚙️ State Management**: Remembers the last processed message to avoid duplicates.

## 🚀 Quick Start

### For Immediate Use
🌍 **Global Collection (Mixed):**
```bash
# Download all collected proxies
curl -s https://raw.githubusercontent.com/mrvcoder/V2rayCollector/main/mixed_iran.txt
```

### 📱 Popular Clients
| Platform | Client | Download |
| :--- | :--- | :--- |
| **Windows/macOS/Linux** | Clash Verge Rev | [📥 Download](https://github.com/clash-verge-rev/clash-verge-rev/releases) |
| **Android** | v2rayNG | [📥 Download](https://github.com/2dust/v2rayNG/releases) |
| **iOS** | V2BOX | [📥 Download](https://apps.apple.com/us/app/v2box-v2ray-client/id1641370530) |
| **Multi-platform** | Hiddify | [📥 Download](https://github.com/hiddify/hiddify-next/releases) |

## 📋 Proxy Collections

| Protocol | Download Link |
| :--- | :--- |
| 🔵 **VMess** | [Download vmess_iran.txt](./vmess_iran.txt) |
| 🟢 **VLess** | [Download vless_iran.txt](./vless_iran.txt) |
| 🔒 **Trojan** | [Download trojan_iran.txt](./trojan_iran.txt) |
| ⚡ **Shadowsocks** | [Download ss_iran.txt](./ss_iran.txt) |
| 🌍 **Mixed** | [Download mixed_iran.txt](./mixed_iran.txt) |
| 🟣 **MTProto** | [Download mtproto_iran.txt](./mtproto_iran.txt) |
| 🟠 **HTTP Proxy** | [Download http_iran.txt](./http_iran.txt) |
| 🟡 **SOCKS Proxy** | [Download socks_iran.txt](./socks_iran.txt) |

## 🛠️ Local Usage

### Prerequisites
- [Go](https://golang.org/) 1.21 or higher

### Running Locally
```bash
# Clone the repository
git clone https://github.com/mrvcoder/V2rayCollector.git
cd V2rayCollector

# Run the collector
go run main.go -sort
```

## 🤝 Contributing

🌟 **Join Our Growing Community!**

- 🔍 **Add New Sources**: Found a reliable Telegram channel? Add it to `channels.csv` and open a PR!
- 🐛 **Report Issues**: Found a bug or have an idea? Create an issue.
- ⭐ **Support**: Star this project to help others discover it!

## 🌟 Recommended Project

Check out this amazing project for more advanced proxy tools:
👉 **[OpenRay](https://github.com/sakha1370/OpenRay)** - A community-driven attempt to keep the internet open and affordable.

## ⚖️ Disclaimer

This project is intended for **educational and research purposes only**.
You are solely responsible for how you use the provided connections. Please respect the terms of service of the source channels and use responsibly in accordance with your local laws.

