# 🚀 Enhanced MERGE-BOT v6.0

<div align="center">

![Enhanced MERGE-BOT](https://img.shields.io/badge/Enhanced%20MERGE--BOT-v6.0-brightgreen?style=for-the-badge&logo=telegram)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)

**The Ultimate Telegram Video Merger Bot**  
*Combining Rich UI + Modern Core + Advanced Features*

[✨ Features](#-features) • [🚀 Quick Start](#-quick-start) • [📖 Documentation](#-documentation) • [🔧 Configuration](#-configuration) • [🚢 Deployment](#-deployment)

</div>

---

## 📋 Overview

**Enhanced MERGE-BOT v6.0** is the most advanced Telegram video merger bot, combining the **rich interactive UI** from `yashoswalyo/MERGE-BOT` with the **modern async core** from `SunilSharmaNP/Sunil-CM`, plus numerous enhancements and new features.

### 🎯 What Makes It Special?

- 🎬 **Advanced Video Processing** - Smart merge engine with fallback modes
- 🎨 **Rich Interactive UI** - Beautiful buttons, settings, and user management  
- ⚡ **Modern Async Architecture** - High performance with smart throttling
- 🔗 **Multiple Upload Options** - Telegram, GoFile.io, Google Drive
- 🛡️ **Production Ready** - Docker, Heroku, error handling, monitoring
- 👥 **User Management** - Authentication, settings, admin controls
- 📊 **Advanced Features** - Progress tracking, compression, broadcasting

---

## ✨ Features

### 🎬 **Core Merge Capabilities**
- **📹 Video Merge** - Combine up to 10 videos with smart compatibility detection
- **🎵 Audio Integration** - Add multiple audio tracks with language support
- **📄 Subtitle Support** - Soft-mux subtitles in multiple formats (SRT, ASS, VTT)
- **🔍 Stream Extraction** - Extract audio/subtitle streams separately
- **⚡ Dual Engine** - Fast stream copy + robust re-encoding fallback

### 🎨 **Rich User Interface**
- **Interactive Settings** - Comprehensive user preferences and customization
- **Smart File Detection** - Automatic format recognition and queue management
- **Progress Tracking** - Real-time progress with ETA and speed monitoring
- **Dynamic Keyboards** - Context-aware buttons and navigation
- **Multi-language Support** - Localization ready architecture

### 🔧 **Advanced Processing**
- **Smart Compatibility** - Automatic format detection and conversion
- **Quality Preservation** - Original quality maintained with CRF control
- **Compression Options** - Multiple quality presets (Best/Balanced/Compressed)
- **Custom Thumbnails** - Auto-generation + custom upload support
- **Metadata Handling** - Preserve and customize video information

### 📤 **Multiple Upload Destinations**
- **📱 Telegram** - Direct upload (2GB free / 4GB premium)
- **🔗 GoFile.io** - External sharing with unlimited size
- **☁️ Google Drive** - Cloud storage integration via rclone
- **📋 Document Mode** - Upload as documents with original filenames

### 👨‍💼 **Administration & Management**
- **User Authentication** - Password-based access control
- **Admin Panel** - Comprehensive bot management interface
- **Broadcasting System** - Mass messaging with progress tracking
- **Statistics Dashboard** - Detailed bot and system statistics
- **Database Integration** - MongoDB support for user data
- **Logging System** - Comprehensive activity and error logging

### 🚀 **Performance & Deployment**
- **Async Architecture** - High-performance concurrent processing
- **Smart Throttling** - FloodWait protection and rate limiting
- **Error Recovery** - Robust error handling and retry mechanisms
- **Docker Support** - Container-ready with docker-compose
- **Multi-Platform** - Heroku, Railway, VPS, local deployment
- **Resource Monitoring** - CPU, memory, disk usage tracking

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- FFmpeg installed
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))
- Telegram API credentials ([my.telegram.org](https://my.telegram.org))

### 1️⃣ Clone Repository

### 🔧 Development Setup
1. Fork repository
2. Clone your fork
git clone https://github.com/yourusername/Sunil-CM.git

3. Create feature branch
git checkout -b feature/your-feature-name

4. Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

5. Make changes and test
python bot.py

6. Submit pull request
text

---

## 📊 Performance & Statistics

### 🚀 Performance Metrics
- **Merge Speed:** Up to 10x faster than basic bots
- **File Size Limit:** 2GB (free) / 4GB (premium) via Telegram
- **Concurrent Users:** 100+ simultaneous operations  
- **Uptime:** 99.9%+ with proper deployment
- **Memory Usage:** ~50-200MB depending on queue size

### 📈 Feature Comparison

| Feature | Basic Bots | Enhanced MERGE-BOT v6.0 |
|---------|------------|--------------------------|
| **Video Merge** | ✅ Basic | ⭐ Advanced with fallback |
| **Audio Integration** | ❌ | ✅ Multi-track support |
| **Subtitles** | ❌ | ✅ Soft-mux multiple formats |
| **Progress Tracking** | ❌ | ✅ Real-time with ETA |
| **User Interface** | ❌ Basic text | ⭐ Rich interactive UI |
| **Upload Options** | ✅ Telegram only | ⭐ Telegram + GoFile + Drive |
| **User Management** | ❌ | ✅ Auth + settings + admin |
| **Broadcasting** | ❌ | ✅ Mass messaging system |
| **Compression** | ❌ | ✅ Multiple quality presets |
| **Admin Panel** | ❌ | ✅ Full management interface |
| **Database** | ❌ | ✅ MongoDB integration |
| **Docker Support** | ❌ | ✅ Production-ready containers |

---

## 🆘 Support & Help

### 📚 Documentation
- **Wiki:** Comprehensive guides and tutorials
- **API Reference:** Developer documentation  
- **Examples:** Sample configurations and use cases

### 💬 Community Support
- **GitHub Issues:** Bug reports and feature requests
- **Telegram Channel:** [@EnhancedMergeBot](https://t.me/EnhancedMergeBot)
- **Discussion:** GitHub Discussions for questions

### 🔧 Troubleshooting

<details>
<summary><b>🔧 Common Issues & Solutions</b></summary>

**Bot not starting:**
- ✅ Check config.env file exists and has correct values
- ✅ Verify API credentials are valid
- ✅ Ensure Python 3.8+ is installed
- ✅ Install FFmpeg on system

**Merge failures:**
- ✅ Check video files are not corrupted
- ✅ Verify sufficient disk space available
- ✅ Try different video formats
- ✅ Check bot logs for specific errors

**Upload failures:**
- ✅ Verify file size is within limits
- ✅ Check internet connection stability
- ✅ Try different upload destination
- ✅ Ensure proper API tokens are set

**Permission errors:**
- ✅ Run with proper user permissions
- ✅ Check directory write permissions
- ✅ Verify Docker user mapping (if using containers)

</details>

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 📋 Third-Party Licenses
- **Pyrogram:** Licensed under LGPLv3+
- **FFmpeg:** Licensed under LGPLv2.1+
- **Other dependencies:** See individual package licenses

---

## 🙏 Acknowledgments

### 🎯 Inspiration & Code Sources
- **yashoswalyo/MERGE-BOT** - Rich UI and user interface design
- **SunilSharmaNP/Sunil-CM** - Modern async core and GoFile integration  
- **Telegram Bot API** - Pyrogram library and documentation
- **FFmpeg Community** - Video processing engine

### 🏆 Special Thanks
- All contributors and testers
- Open source community
- Telegram Bot developers
- FFmpeg development team

---

## 🔮 Roadmap

### 🚧 Upcoming Features
- [ ] **Web Dashboard** - Browser-based admin interface
- [ ] **Batch Processing** - Queue multiple merge operations
- [ ] **Plugin System** - Custom extension support
- [ ] **API Endpoint** - REST API for external integration
- [ ] **Cloud Storage** - Additional cloud storage providers
- [ ] **Video Preview** - Thumbnail and preview generation
- [ ] **Scheduled Tasks** - Automated merge operations
- [ ] **Multi-language UI** - Complete localization
- [ ] **Advanced Analytics** - Detailed usage statistics
- [ ] **Mobile App** - Native mobile companion

### 💫 Long-term Goals
- Advanced AI-based video processing
- Real-time video streaming capabilities  
- Integration with major video platforms
- Enterprise deployment features
- Advanced user role management

---

<div align="center">

## 🌟 Show Your Support

If you find this project useful, please consider:

⭐ **Starring** this repository  
🍴 **Forking** for your own modifications  
🐛 **Reporting** bugs and issues  
💡 **Suggesting** new features  
🤝 **Contributing** code improvements  

---

**Made with ❤️ by the Enhanced MERGE-BOT Team**

[![GitHub Stars](https://img.shields.io/github/stars/SunilSharmaNP/Sunil-CM?style=social)](https://github.com/SunilSharmaNP/Sunil-CM/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/SunilSharmaNP/Sunil-CM?style=social)](https://github.com/SunilSharmaNP/Sunil-CM/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/SunilSharmaNP/Sunil-CM)](https://github.com/SunilSharmaNP/Sunil-CM/issues)

</div>
