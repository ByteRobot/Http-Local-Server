# ✨ Face Blur Studio Pro

<div align="center">

**Professional Face Detection & Blurring Solution**

*Automated privacy protection for images and videos with advanced AI-powered face detection*

<p align="center">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-00D4FF?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Version-1.0.0-8A2BE2?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/OpenCV-4.x-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" />
  <img src="https://img.shields.io/badge/MediaPipe-Enabled-FF6F00?style=for-the-badge&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/FFmpeg-Audio%20Preservation-000000?style=for-the-badge&logo=ffmpeg&logoColor=white" />
</p>

[Features](#-key-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-usage-guide) • [Build](#-build-executable)

</div>

---

## 🎯 Overview

Face Blur Studio Pro is a cutting-edge desktop application designed for creators, journalists, researchers, and organizations who need to protect privacy through precise face detection and blurring. Built with enterprise-grade AI and optimized for performance, it handles everything from single portraits to large group photos and full-length videos.

### Why Choose Face Blur Studio Pro?

- **AI-Powered Detection**: Dual MediaPipe detectors with Haar cascade fallback for maximum accuracy
- **Production-Ready**: Triple-layer Gaussian blur ensures complete anonymization
- **Professional Workflow**: Batch processing, real-time preview, and progress tracking
- **Media Integrity**: Preserves PNG transparency and video audio tracks
- **GDPR Compliant**: Perfect for privacy-sensitive workflows

---

## 🖼️ Application Preview

<div align="center">

### Dark-Themed Professional Interface

<img width="761" height="503" alt="img" src="https://github.com/user-attachments/assets/4cade144-7831-44c8-8b98-23a109f15eee" />


*Featuring drag-and-drop functionality, real-time preview with optional debug visualization, and intuitive controls for precision face detection*

</div>

**Interface Highlights:**
- 🎨 **Modern Dark Theme** - Eye-friendly design for extended use
- 📁 **Drag & Drop** - Effortless file selection
- 👁️ **Live Preview** - See results before processing
- 🎯 **Debug Mode** - Visualize detected face regions with bounding boxes
- 📊 **Progress Tracking** - Real-time status updates and completion indicators

---

## ⭐ Key Features

### Detection & Processing
- **Multi-Face Detection** - Unlimited faces per frame with intelligent deduplication
- **Adaptive Blur Kernel** - Automatically scales to 40% of face size
- **Dual-Pass Detection** - MediaPipe primary + Haar cascade fallback (Group Photo Mode)
- **Smart Padding** - Extended coverage (30% horizontal, 40% vertical)
- **Range Selection** - Short Range (0-2m) for portraits, Full Range (2-5m) for groups

### Media Support
- **Image Formats** - JPG, PNG, BMP, WebP, TIFF (preserves PNG transparency)
- **Video Formats** - MP4, MOV, AVI, MKV, WebM, FLV, WMV
- **Audio Preservation** - FFmpeg integration with AAC 192 kbps encoding
- **High Resolution** - Optimized for 4K processing

### User Experience
- **Intuitive GUI** - PyQt5-powered responsive interface with tooltips
- **Real-Time Feedback** - Live progress bars and status messages
- **Error Resilience** - Comprehensive error handling and automatic cleanup
- **Cancellation Support** - Stop processing anytime without corruption
- **Cross-Platform** - Windows, macOS, and Linux compatible

---

## 📚 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
- [Optimal Settings](#-optimal-settings)
- [Supported Formats](#-supported-formats)
- [Performance Metrics](#-performance-metrics)
- [Technical Architecture](#-technical-architecture)
- [Build Executable](#-build-executable)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- FFmpeg (optional, for video audio preservation)

### Step 1: Clone Repository
```bash
git clone https://github.com/Al-Baddar/face-blur-studio-pro.git
cd face-blur-studio-pro
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

**Or install packages individually:**
```bash
pip install PyQt5 opencv-python mediapipe numpy
```

### Step 3: Install FFmpeg (Recommended)

<details>
<summary><b>Windows</b></summary>

```bash
winget install ffmpeg
```
Or download from [ffmpeg.org](https://ffmpeg.org/download.html)
</details>

<details>
<summary><b>macOS</b></summary>

```bash
brew install ffmpeg
```
</details>

<details>
<summary><b>Linux (Ubuntu/Debian)</b></summary>

```bash
sudo apt update
sudo apt install ffmpeg
```
</details>

**Verify installation:**
```bash
ffmpeg -version
```

---

## 🚀 Quick Start

### Launch Application
```bash
python main.py
```

### Basic Workflow
1. **Import Media** - Drag & drop a file or click "Browse Files"
2. **Configure Settings** - Adjust Confidence and Detection Range
3. **Enable Group Mode** (Optional) - For wide shots with multiple faces
4. **Preview** - Use "Show Debug Boxes" to verify detection
5. **Process** - Click "Start Blur" and monitor progress
6. **Export** - Use "Open Output Folder" to access results

---

## 📖 Usage Guide

### Configuration Parameters

#### **Confidence Threshold**
Controls face detection sensitivity (0-100%)
- **Lower values (25-40%)**: Detect more faces, may include false positives
- **Higher values (50-70%)**: Stricter detection, fewer false positives
- **Recommended**: 30-35% for group photos, 50-60% for portraits

#### **Detection Range**
Optimizes face detection distance
- **Short Range (0-2m)**: Best for close-up shots and portraits
- **Full Range (2-5m)**: Ideal for group photos and wide shots

#### **Group Photo Mode**
Advanced dual-detection system
- Runs MediaPipe (short + full range) + Haar cascade in parallel
- Deduplicates overlapping detections
- Applies intelligent padding for complete coverage
- Slightly slower but significantly more accurate for crowded scenes

#### **Show Debug Boxes**
Visual debugging tool
- Displays green rectangles over detected face regions
- Useful for verifying detection before processing
- Toggle on/off for preview testing

---

## 🎯 Optimal Settings

### Scenario-Based Configuration

<table>
<tr>
<th>Use Case</th>
<th>Confidence</th>
<th>Range</th>
<th>Group Mode</th>
<th>Notes</th>
</tr>
<tr>
<td><b>Wide Group Photos</b><br/><i>Wedding, conference, team photo</i></td>
<td>25-35%</td>
<td>Full Range</td>
<td>✅ On</td>
<td>Detects small/distant faces</td>
</tr>
<tr>
<td><b>Portrait/Headshots</b><br/><i>Profile pictures, ID photos</i></td>
<td>50-70%</td>
<td>Short Range</td>
<td>❌ Off</td>
<td>Faster processing</td>
</tr>
<tr>
<td><b>Street Photography</b><br/><i>Candid shots, events</i></td>
<td>35-45%</td>
<td>Full Range</td>
<td>✅ On</td>
<td>Balanced detection</td>
</tr>
<tr>
<td><b>Video Interviews</b><br/><i>Single/dual subjects</i></td>
<td>45-55%</td>
<td>Short Range</td>
<td>❌ Off</td>
<td>Real-time performance</td>
</tr>
<tr>
<td><b>Crowded Scenes</b><br/><i>Protests, concerts, markets</i></td>
<td>25-30%</td>
<td>Full Range</td>
<td>✅ On</td>
<td>Maximum coverage</td>
</tr>
</table>

---

## 📦 Supported Formats

### Images
| Format | Extensions | Features |
|--------|-----------|----------|
| JPEG | `.jpg`, `.jpeg` | Lossy compression, universal support |
| PNG | `.png` | Lossless, **transparency preserved** |
| BMP | `.bmp` | Uncompressed bitmap |
| WebP | `.webp` | Modern compression |
| TIFF | `.tiff`, `.tif` | High-quality archival |

### Videos
| Format | Extension | Audio Support |
|--------|-----------|---------------|
| MP4 | `.mp4` | ✅ AAC 192 kbps |
| MOV | `.mov` | ✅ AAC 192 kbps |
| AVI | `.avi` | ✅ AAC 192 kbps |
| MKV | `.mkv` | ✅ AAC 192 kbps |
| WebM | `.webm` | ✅ AAC 192 kbps |
| FLV | `.flv` | ✅ AAC 192 kbps |
| WMV | `.wmv` | ✅ AAC 192 kbps |

**Note**: Audio preservation requires FFmpeg installation

---

## ⚡ Performance Metrics

### Benchmarks
<table>
<tr>
<th>Media Type</th>
<th>Resolution</th>
<th>Processing Speed</th>
<th>Face Capacity</th>
<th>Hardware</th>
</tr>
<tr>
<td>Image</td>
<td>1920×1080</td>
<td>1-3 seconds</td>
<td>≤ 50 faces</td>
<td>Mid-range CPU</td>
</tr>
<tr>
<td>Video (HD)</td>
<td>1080p @ 30fps</td>
<td>0.5-1× realtime</td>
<td>Unlimited</td>
<td>Mid-range CPU</td>
</tr>
<tr>
<td>Video (4K)</td>
<td>2160p @ 30fps</td>
<td>0.3-0.7× realtime</td>
<td>Unlimited</td>
<td>High-end CPU</td>
</tr>
<tr>
<td>Batch (100 images)</td>
<td>1920×1080</td>
<td>3-5 minutes</td>
<td>Variable</td>
<td>Mid-range CPU</td>
</tr>
</table>

### Performance Tips
- **Close Unnecessary Apps** - Free up system resources
- **Use Short Range** - For single-subject videos (2x faster)
- **Disable Group Mode** - When detecting large faces only
- **SSD Storage** - Significantly faster I/O for video processing

---

## 🏗️ Technical Architecture

### Technology Stack
```
┌─────────────────────────────────────┐
│         User Interface Layer        │
│          PyQt5 (Dark Theme)         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       Application Logic Layer       │
│    MVC Pattern + QThread Workers    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Computer Vision Engine         │
│  MediaPipe + OpenCV + Haar Cascade  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        Media Processing Layer       │
│   NumPy Arrays + FFmpeg Integration │
└─────────────────────────────────────┘
```

### Detection Pipeline
1. **Frame Extraction** - OpenCV video/image loading
2. **Primary Detection** - MediaPipe face detection (Short/Full Range)
3. **Fallback Detection** - Haar Cascade (Group Photo Mode only)
4. **Deduplication** - IoU-based overlap removal
5. **Padding Application** - 30% horizontal, 40% vertical expansion
6. **Blur Processing** - Triple-layer Gaussian blur (kernel = 40% face size)
7. **Frame Reconstruction** - Blurred regions composited onto original
8. **Audio Merging** - FFmpeg AAC encoding and stream synchronization

### Project Structure
```
face-blur-studio-pro/
├── main.py                 # GUI application entry point
├── face_blur_worker.py     # Core processing engine
│   ├── FaceBlurWorker      # QThread worker class
│   ├── MediaPipe detectors # Short/Full range models
│   ├── Haar cascade        # Fallback detector
│   └── FFmpeg wrapper      # Audio preservation
├── requirements.txt        # Python dependencies
├── README.md              # Documentation (this file)
└── .gitignore             # Version control exclusions
```

---

## 📦 Build Executable

### Create Standalone Application

Install PyInstaller:
```bash
pip install pyinstaller
```

Build executable:
```bash
pyinstaller --noconfirm \
            --onefile \
            --windowed \
            --name "FaceBlurStudioPro" \
            --icon=icon.ico \
            main.py
```

**Output Location**: `dist/FaceBlurStudioPro.exe` (Windows) or `dist/FaceBlurStudioPro` (macOS/Linux)

### Distribution Notes
- **FFmpeg Requirement**: End users must install FFmpeg separately for video audio support
- **Python Not Required**: Executable bundles Python interpreter
- **File Size**: Approximately 150-250 MB (includes MediaPipe models)
- **First Launch**: May take 5-10 seconds to initialize MediaPipe

### Advanced Build Options
```bash
# Include custom icon
--icon=path/to/icon.ico

# Add version info (Windows)
--version-file=version.txt

# Bundle additional data files
--add-data "models:models"

# Optimize size
--strip
```

### PyInstaller (EXE-friendly build with Haar Cascade)

To ensure OpenCV’s Haar cascade loads correctly inside the EXE, bundle the XML file.

1) Copy Haar cascade file to project root (same folder as `main.py`):
```bash
python -c "import cv2; print(cv2.data.haarcascades)"
# Open the printed folder and copy: haarcascade_frontalface_default.xml
# Paste it next to main.py
```

2) Build the EXE with data and hidden imports:
```bash
pyinstaller --onefile --windowed --name FaceBlurStudioPro \
  --hidden-import=mediapipe \
  --hidden-import=cv2 \
  --hidden-import=face_blur_worker \
  --collect-data=mediapipe \
  --collect-submodules=mediapipe \
  --add-data "haarcascade_frontalface_default.xml;." \
  main.py
```

Windows CMD (caret for line breaks):
```bash
pyinstaller --onefile --windowed --name FaceBlurStudioPro ^
--hidden-import=mediapipe ^
--hidden-import=cv2 ^
--hidden-import=face_blur_worker ^
--collect-data=mediapipe ^
--collect-submodules=mediapipe ^
--add-data "haarcascade_frontalface_default.xml;." ^
main.py
```

3) Run the EXE:
```
dist/
└── FaceBlurStudioPro.exe  # Windows
```

Optional debug build (shows console errors):
```bash
pyinstaller --onefile --console --name FaceBlurStudioPro \
  --add-data "haarcascade_frontalface_default.xml;." \
  main.py
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

<details>
<summary><b>�� Faces Not Detected in Wide Group Photos</b></summary>

**Solutions:**
1. Lower confidence threshold to 25-35%
2. Switch to "Full Range (2-5m)" detection
3. Enable "Group Photo Mode"
4. Verify faces are clearly visible (not obscured)
5. Try increasing image brightness/contrast
</details>

<details>
<summary><b>🔇 Processed Video Has No Audio</b></summary>

**Solutions:**
1. Install FFmpeg: `ffmpeg -version` should return version info
2. Add FFmpeg to system PATH
3. Restart the application after installing FFmpeg
4. Check original video has audio track
5. Verify disk space for temporary files
</details>

<details>
<summary><b>🖼️ PNG Transparency Lost After Processing</b></summary>

**Solutions:**
1. Ensure output file has `.png` extension (automatic if input is PNG)
2. Verify input PNG actually contains alpha channel
3. Check OpenCV installation supports PNG with transparency
4. Try re-saving source PNG in image editor
</details>

<details>
<summary><b>🚫 Application Won't Launch</b></summary>

**Solutions:**
1. Verify Python 3.8+: `python --version`
2. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
3. Check for conflicting PyQt5 installations
4. Run from terminal to see error messages: `python main.py`
5. Try creating fresh virtual environment
</details>

<details>
<summary><b>⚠️ Detection Too Slow on High-Resolution Video</b></summary>

**Solutions:**
1. Disable "Group Photo Mode" if not needed
2. Use "Short Range" for single subjects
3. Close background applications
4. Consider downscaling video to 1080p before processing
5. Process on machine with better CPU
</details>

<details>
<summary><b>📉 Low Detection Accuracy</b></summary>

**Solutions:**
1. Ensure adequate lighting in source media
2. Avoid extreme angles (>45° profile)
3. Minimum face size: 20x20 pixels
4. Check for motion blur in video frames
5. Use Group Photo Mode for challenging scenes
</details>

### Getting Help
If issues persist:
- Open an issue on [GitHub Issues](https://github.com/Al-Baddar/face-blur-studio-pro/issues)
- Include: OS version, Python version, error messages, sample media (if possible)
- Check existing issues for solutions

---

## 🗺️ Roadmap

### Version 1.1 (Q2 2025)
- [ ] **Batch Processing Queue** - Process multiple files sequentially
- [ ] **Custom Blur Effects** - Mosaic, pixelation, black bars, emoji overlay
- [ ] **Manual Selection Mode** - Click to add/remove face regions

### Version 1.2 (Q3 2025)
- [ ] **GPU Acceleration** - CUDA (NVIDIA) and Metal (Apple Silicon) support
- [ ] **CLI Version** - Command-line interface for automation/scripting
- [ ] **Export Presets** - Save/load configuration profiles

### Version 2.0 (Q4 2025)
- [ ] **Plugin System** - Extend functionality with custom modules
- [ ] **Body Blurring** - Full-body detection and anonymization
- [ ] **License Plate Detection** - Automatic vehicle plate blurring
- [ ] **Cloud Processing** - Optional cloud API for heavy workloads

### Future Considerations
- Real-time webcam blurring
- Browser extension version
- Mobile app (iOS/Android)
- Object detection (not just faces)
- Multi-language support

**Want to contribute?** Check our [Contributing Guidelines](CONTRIBUTING.md) and open a pull request!

---

## 📜 License

### Application License
This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Al-Baddar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:


```

### Third-Party Licenses
- **MediaPipe**: Apache 2.0 License (Google LLC)
- **OpenCV**: Apache 2.0 License
- **PyQt5**: GPLv3 or Commercial License
- **FFmpeg**: LGPLv2.1+ or GPLv2+ (depending on build)

**Commercial Use**: If distributing commercially, ensure compliance with PyQt5 licensing (consider commercial license or use PySide6 as alternative).

---

## 🙏 Acknowledgements

This project wouldn't be possible without these amazing open-source technologies:

- **[Google MediaPipe](https://mediapipe.dev/)** - State-of-the-art face detection models
- **[OpenCV](https://opencv.org/)** - Comprehensive computer vision library
- **[FFmpeg](https://ffmpeg.org/)** - Industry-standard multimedia framework
- **[Qt/PyQt5](https://www.riverbankcomputing.com/software/pyqt/)** - Powerful cross-platform GUI framework
- **[NumPy](https://numpy.org/)** - Fundamental package for scientific computing

Special thanks to the open-source community for continuous innovation in computer vision and AI.

---

## 👥 Contributors

### Maintainer
**Al-Baddar**
- GitHub: [@Al-Baddar](https://github.com/Al-Baddar)
- Project: [face-blur-studio-pro](https://github.com/Al-Baddar/face-blur-studio-pro)

### Contributing
We welcome contributions! Here's how you can help:

1. **🐛 Report Bugs** - Open an issue with details and screenshots
2. **💡 Suggest Features** - Share your ideas in discussions
3. **📖 Improve Documentation** - Fix typos, add examples
4. **💻 Submit Code** - Fork, develop, and create pull requests

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 🌟 Show Your Support

If you find Face Blur Studio Pro useful:

- ⭐ **Star this repository** to help others discover it
- 🐦 **Share on social media** with #FaceBlurStudioPro
- 💬 **Spread the word** to colleagues and friends
- 🤝 **Contribute** via issues, PRs, or feedback

**Your support motivates continued development!**

---

<div align="center">

**Made by M.Hashir for privacy-conscious creators worldwide**

[Report Bug](https://github.com/Al-Baddar/face-blur-studio-pro/issues) • [Request Feature](https://github.com/Al-Baddar/face-blur-studio-pro/issues) • [Documentation](https://github.com/Al-Baddar/face-blur-studio-pro/wiki)

---

*Face Blur Studio Pro v1.0.0 | © 2025 Al-Baddar | MIT License*

</div>
