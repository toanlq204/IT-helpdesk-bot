#!/usr/bin/env python3
"""
TTS Dependencies Installation Script
==================================

This script installs the optional TTS (Text-to-Speech) dependencies
for the IT Helpdesk Bot voice features.

Dependencies installed:
- transformers: Hugging Face transformers library
- torch: PyTorch for model inference
- soundfile: Audio file handling
- datasets: Dataset utilities for TTS models

Usage:
    python install_tts.py
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def install_torch_alternative():
    """Try alternative torch installation methods for corporate environments"""
    print("Trying alternative PyTorch installation methods...")
    
    # Method 1: Try CPU-only PyTorch from official source
    torch_commands = [
        # CPU-only version (smaller, faster download)
        "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu",
        # Standard PyPI (fallback)
        "pip install torch --no-deps",
        # Conda if available
        "conda install pytorch cpuonly -c pytorch"
    ]
    
    for i, cmd in enumerate(torch_commands, 1):
        try:
            print(f"Method {i}: {cmd}")
            subprocess.check_call(cmd.split())
            print("✅ PyTorch installed successfully!")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ Method {i} failed, trying next...")
            continue
    
    return False

def main():
    """Main installation function"""
    print("🔊 Installing TTS Dependencies for IT Helpdesk Bot")
    print("=" * 50)
    
    # Split packages into torch and non-torch
    standard_packages = [
        "transformers>=4.21.0",
        "soundfile>=0.12.1", 
        "datasets>=2.4.0"
    ]
    
    success_count = 0
    
    # Install standard packages first
    for package in standard_packages:
        if install_package(package):
            success_count += 1
        print()
    
    # Try torch installation with alternatives
    print("Installing PyTorch (may require special handling)...")
    if install_torch_alternative():
        success_count += 1
    else:
        print("⚠️  PyTorch installation failed. Trying minimal alternatives...")
        # Try installing without torch for basic functionality
        if install_package("numpy>=1.21.0"):
            print("📝 Installed numpy as fallback for basic operations")
    
    total_packages = len(standard_packages) + 1  # +1 for torch
    print(f"Installation Summary: {success_count}/{total_packages} packages installed")
    
    if success_count == total_packages:
        print("🎉 All TTS dependencies installed successfully!")
        print("\nYou can now use voice features in the IT Helpdesk Bot:")
        print("- Enable TTS in the sidebar")
        print("- Click 🔊 buttons to hear responses")
        print("- Enable auto-play for automatic speech")
    elif success_count >= len(standard_packages):
        print("✅ Core TTS dependencies installed!")
        print("⚠️  PyTorch may need manual installation for full functionality")
        print("\nFor PyTorch in corporate environments, try:")
        print("pip install torch --index-url https://download.pytorch.org/whl/cpu")
    else:
        print("⚠️  Some packages failed to install.")
        print("Voice features may not work properly.")
        print("\nTry running: pip install transformers torch soundfile datasets")

if __name__ == "__main__":
    main()
