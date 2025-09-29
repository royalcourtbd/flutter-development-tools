# Flutter Development Tools 🚀

Advanced Flutter development utilities with **AI-powered commit messages** that work on **macOS**, **Linux**, and **Windows**.

## 💫 Prerequisites

- **Python 3.6+** installed and available in PATH
- **Flutter SDK** installed and configured
- **Git** installed and configured
- **Internet connection** (for AI features)
- **Google Gemini API access** (for AI commit messages)

## 🚀 Quick Setup

### 1. Download/Clone this repository
```bash
git clone <repository-url>
cd flutter-tools
```

### 2. Run setup script
```bash
python3 setup.py    # macOS/Linux
python setup.py     # Windows
```

### 3. Follow the instructions
The setup script will:
- Create necessary directories
- Install scripts globally
- Set up PATH (with instructions)

## 💡 Quick Usage Examples

```bash
# AI-powered commit
flutter-dev commit              # Generate smart commit message with AI

# Build and deploy
flutter-dev apk                 # Build release APK
flutter-dev release-run         # Build and install on device

# Project maintenance
flutter-dev setup               # Full project setup
flutter-dev cleanup             # Clean and refresh dependencies

# Page generation
flutter-dev page login          # Create login page structure

# Version management
flutter-dev tag                 # Create git tag from pubspec version
```

## 📱 Available Commands

### Build Commands
```bash
flutter-dev apk              # Build release APK (Full Process)
flutter-dev apk-split        # Build APK with --split-per-abi
flutter-dev aab              # Build release AAB
flutter-dev release-run      # Build & install APK on device
```

### Development Commands
```bash
flutter-dev setup            # Full project setup
flutter-dev cleanup          # Clean project and get dependencies
flutter-dev db               # Run build_runner
flutter-dev lang             # Generate localization files
flutter-dev cache-repair     # Repair pub cache
```

### iOS Commands
```bash
flutter-dev pod              # Update iOS pods (macOS only)
```

### Git Commands 🤖
```bash
flutter-dev tag              # Create and push git tag from pubspec version
flutter-dev commit           # Smart git commit with AI-generated message
```

### Project Generation
```bash
flutter-dev page user_profile       # Via flutter-dev command
create-page page user_profile       # Direct command
```

### Device Commands
```bash
flutter-dev uninstall        # Uninstall app from connected device
```

## 🤖 AI Features

### Smart Commit Messages
The `flutter-dev commit` command uses **Google Gemini AI** to generate professional commit messages:

```bash
flutter-dev commit
```

**Features:**
- 🎯 **Conventional Commits**: Follows Angular format (`feat:`, `fix:`, `docs:`, etc.)
- 📝 **Automatic Analysis**: Analyzes your git diff to understand changes
- 🎨 **Smart Formatting**: Adds bullet points to description lines
- ✅ **Review & Confirm**: Shows generated message before committing
- 🔄 **Auto-staging**: Stages unstaged changes if needed

**Example Output:**
```
Generated commit message:
feat(auth): implement user login with validation 🔐

- Added email and password input fields with real-time validation
- Integrated Firebase Authentication for secure user login
- Added loading states and error handling for better UX
- Implemented remember me functionality with secure storage

Proceed with this commit? (y/N):
```

## 🔧 Platform-Specific Notes

### Windows
- Commands available as: `flutter-dev.bat`, `create-page.bat`
- Uses batch wrappers for cross-platform compatibility
- Add `%USERPROFILE%\bin` to your PATH

### macOS/Linux
- Commands available as: `flutter-dev`, `create-page`
- Uses symlinks for better performance
- Add `$HOME/bin` to your PATH

## 📁 File Structure

```
~/scripts/flutter-tools/
├── flutter-dev.py          # Main utility script with AI features
├── create_page.py          # Page generator script
├── gemini_api.py          # Google Gemini AI integration
├── git_diff_output_editor.py # Git diff processing utilities
├── setup.py               # Cross-platform setup
└── README.md              # This file

~/bin/                     # Global commands
├── flutter-dev[.bat]      # Main command
└── create-page[.bat]      # Page generator
```

## 🔄 Updates

To update the tools:

1. **Edit the master files:**
   - `~/scripts/flutter-tools/flutter-dev.py`
   - `~/scripts/flutter-tools/create_page.py`
   - `~/scripts/flutter-tools/gemini_api.py`

2. **Changes are automatically available globally!**

### AI Configuration
The Gemini AI features use Google's Gemini API. The API key is configured in `gemini_api.py`.

## 🐛 Troubleshooting

### Command not found
- **Windows**: Make sure `%USERPROFILE%\bin` is in your PATH
- **macOS/Linux**: Make sure `$HOME/bin` is in your PATH
- Restart your terminal after PATH changes

### Permission denied (macOS/Linux)
```bash
chmod +x ~/scripts/flutter-tools/*.py
chmod +x ~/bin/flutter-dev ~/bin/create-page
```

### Python not found
Make sure Python 3 is installed and available in your PATH.

### Flutter project not detected
Make sure you're running commands from the root of a Flutter project (where `pubspec.yaml` exists).

### AI commit message generation fails
- Check your internet connection
- Verify the Gemini API key in `gemini_api.py`
- Make sure you have git changes to analyze
- Try running `python3 gemini_api.py` to test the API connection

## 🎯 Features

### Core Features
- ✅ **Cross-platform** - Works on macOS, Linux, Windows
- ✅ **Global access** - Use from any Flutter project directory
- ✅ **Auto-updates** - Edit once, use everywhere
- ✅ **Clean architecture** - Separate concerns, maintainable
- ✅ **Flutter project detection** - Prevents running in wrong directories
- ✅ **Time tracking** - Shows how long operations take
- ✅ **Color output** - Easy to read terminal output
- ✅ **Error handling** - Graceful error messages and recovery

### AI-Powered Features 🤖
- 🎯 **Smart Commits** - AI-generated commit messages using Google Gemini
- 📝 **Conventional Format** - Follows industry-standard commit conventions
- 🔍 **Code Analysis** - Automatically analyzes git diffs to understand changes
- ✨ **Professional Output** - Clean, formatted commit messages with bullet points
- 🔄 **Interactive Workflow** - Review and confirm before committing

### Development Utilities
- 📦 **Build Management** - APK, AAB, split builds
- 📱 **Device Management** - Install, uninstall, release builds
- 🌍 **Localization** - Generate language files
- 🗺 **Page Generation** - Create Flutter page structures
- 🧹 **Project Maintenance** - Cleanup, cache repair, dependency management
- 🏷 **Version Control** - Git tagging from pubspec version

## 📝 License

MIT License - feel free to modify and distribute!
