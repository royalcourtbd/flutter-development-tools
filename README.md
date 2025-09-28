# Flutter Development Tools

Cross-platform Flutter development utilities that work on **macOS**, **Linux**, and **Windows**.

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

### Git Commands
```bash
flutter-dev tag              # Create and push git tag from pubspec version
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
├── flutter-dev.py       # Main utility script
├── create_page.py       # Page generator script
├── setup.py            # Cross-platform setup
└── README.md           # This file

~/bin/                  # Global commands
├── flutter-dev[.bat]   # Main command
└── create-page[.bat]   # Page generator
```

## 🔄 Updates

To update the tools:

1. **Edit the master files:**
   - `~/scripts/flutter-tools/flutter-dev.py`
   - `~/scripts/flutter-tools/create_page.py`

2. **Changes are automatically available globally!**

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

## 🎯 Features

- ✅ **Cross-platform** - Works on macOS, Linux, Windows
- ✅ **Global access** - Use from any Flutter project directory
- ✅ **Auto-updates** - Edit once, use everywhere
- ✅ **Clean architecture** - Separate concerns, maintainable
- ✅ **Flutter project detection** - Prevents running in wrong directories
- ✅ **Time tracking** - Shows how long operations take
- ✅ **Color output** - Easy to read terminal output
- ✅ **Error handling** - Graceful error messages and recovery

## 📝 License

MIT License - feel free to modify and distribute!
