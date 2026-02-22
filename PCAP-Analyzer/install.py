#!/usr/bin/env python3
"""
PCAP Analyzer - Universal Installer
Works on Windows, macOS, and Linux
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m' if platform.system() != 'Windows' else ''
    YELLOW = '\033[93m' if platform.system() != 'Windows' else ''
    RED = '\033[91m' if platform.system() != 'Windows' else ''
    BLUE = '\033[94m' if platform.system() != 'Windows' else ''
    RESET = '\033[0m' if platform.system() != 'Windows' else ''

def print_step(msg):
    print(f"{Colors.BLUE}[*]{Colors.RESET} {msg}")

def print_success(msg):
    print(f"{Colors.GREEN}[✓]{Colors.RESET} {msg}")

def print_error(msg):
    print(f"{Colors.RED}[✗]{Colors.RESET} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}[!]{Colors.RESET} {msg}")

def check_python_version():
    """Check if Python version is 3.7+"""
    print_step("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print_error(f"Python 3.7+ required. You have {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """Install required Python packages"""
    print_step("Installing Python dependencies...")
    
    packages = [
        'scapy',
        'matplotlib',
        'networkx',
        'ipwhois',
        'requests'
    ]
    
    try:
        for package in packages:
            print(f"  Installing {package}...")
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', '--quiet', package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        print_success("All dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False

def get_install_paths():
    """Get platform-specific installation paths"""
    system = platform.system()
    home = Path.home()
    
    if system == 'Windows':
        tools_dir = home / '.pcap_tools'
        output_dir = home / 'Desktop' / 'pcap_analysis_output'
        bin_dir = Path(os.environ.get('LOCALAPPDATA', home)) / 'Programs' / 'pcap-analyzer'
        wrapper_name = 'analyze.bat'
    else:  # macOS/Linux
        tools_dir = home / '.pcap_tools'
        output_dir = home / 'Desktop' / 'pcap_analysis_output'
        bin_dir = Path('/usr/local/bin')
        wrapper_name = 'analyze'
    
    return tools_dir, output_dir, bin_dir, wrapper_name

def copy_files(tools_dir):
    """Copy analyzer files to installation directory"""
    print_step("Copying analyzer files...")
    
    # Create directory
    tools_dir.mkdir(parents=True, exist_ok=True)
    
    # Files to copy
    files = [
        'pcap_analyzer_v3.py',
        'aws_detection.py',
        'security_analysis.py'
    ]
    
    script_dir = Path(__file__).parent
    
    for file in files:
        src = script_dir / file
        dst = tools_dir / file
        
        if not src.exists():
            print_error(f"File not found: {file}")
            return False
        
        shutil.copy2(src, dst)
        print(f"  Copied {file}")
    
    # Make main script executable on Unix
    if platform.system() != 'Windows':
        (tools_dir / 'pcap_analyzer_v3.py').chmod(0o755)
    
    print_success("Files copied")
    return True

def create_wrapper(tools_dir, bin_dir, wrapper_name):
    """Create command wrapper"""
    print_step("Creating command wrapper...")
    
    system = platform.system()
    wrapper_path = bin_dir / wrapper_name
    
    if system == 'Windows':
        # Create batch file
        content = f'''@echo off
python "{tools_dir / 'pcap_analyzer_v3.py'}" %*
'''
        bin_dir.mkdir(parents=True, exist_ok=True)
        wrapper_path.write_text(content)
        
        # Add to PATH if not already there
        add_to_windows_path(bin_dir)
        
    else:  # macOS/Linux
        # Create bash wrapper
        content = f'''#!/bin/bash
python3 "{tools_dir / 'pcap_analyzer_v3.py'}" "$@"
'''
        try:
            # Try to write to /usr/local/bin (requires sudo)
            if os.access(bin_dir, os.W_OK):
                wrapper_path.write_text(content)
                wrapper_path.chmod(0o755)
            else:
                # Need sudo
                print_warning("Need administrator privileges to install to /usr/local/bin")
                temp_file = Path('/tmp/analyze')
                temp_file.write_text(content)
                subprocess.run(['sudo', 'mv', str(temp_file), str(wrapper_path)], check=True)
                subprocess.run(['sudo', 'chmod', '+x', str(wrapper_path)], check=True)
        except Exception as e:
            print_error(f"Failed to create wrapper: {e}")
            return False
    
    print_success(f"Command wrapper created: {wrapper_path}")
    return True

def add_to_windows_path(bin_dir):
    """Add directory to Windows PATH"""
    if platform.system() != 'Windows':
        return
    
    try:
        import winreg
        
        # Get current user PATH
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ | winreg.KEY_WRITE)
        current_path, _ = winreg.QueryValueEx(key, 'Path')
        
        bin_dir_str = str(bin_dir)
        if bin_dir_str not in current_path:
            new_path = f"{current_path};{bin_dir_str}"
            winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
            print_success("Added to PATH (restart terminal to use)")
        
        winreg.CloseKey(key)
    except Exception as e:
        print_warning(f"Could not add to PATH automatically: {e}")
        print_warning(f"Manually add to PATH: {bin_dir}")

def create_output_directory(output_dir):
    """Create output directory"""
    print_step("Creating output directory...")
    output_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"Output directory: {output_dir}")
    return True

def test_installation():
    """Test if installation works"""
    print_step("Testing installation...")
    
    try:
        result = subprocess.run(
            ['analyze', '--help'] if platform.system() != 'Windows' else ['analyze.bat', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if '--aws' in result.stdout and '--security' in result.stdout:
            print_success("Installation test passed")
            return True
        else:
            print_warning("Installation may be incomplete (AWS/security flags not found)")
            return True
    except FileNotFoundError:
        print_warning("Command not found in PATH yet. Restart terminal and try: analyze --help")
        return True
    except Exception as e:
        print_error(f"Test failed: {e}")
        return False

def print_usage_instructions():
    """Print usage instructions"""
    system = platform.system()
    cmd = 'analyze' if system != 'Windows' else 'analyze.bat'
    
    print(f"\n{Colors.GREEN}{'='*60}{Colors.RESET}")
    print(f"{Colors.GREEN}Installation Complete!{Colors.RESET}")
    print(f"{Colors.GREEN}{'='*60}{Colors.RESET}\n")
    
    print("Usage:")
    print(f"  {cmd} capture.pcap")
    print(f"  {cmd} capture.pcap --aws --security")
    print(f"  {cmd} capture.pcap --visual --export-json")
    print(f"  {cmd} capture.pcap --aws --security --visual --export-json\n")
    
    print("Available flags:")
    print("  --aws          AWS-specific analysis (ELB, IMDS, NAT, TGW)")
    print("  --security     Security analysis (SG blocks, RST, DDoS, scans)")
    print("  --visual       Generate PNG diagrams and HTML report")
    print("  --export-json  Export data to JSON file")
    print("  --whois        Perform IP geolocation lookups")
    print("  --tor          Check for Tor exit nodes\n")
    
    if system == 'Windows':
        print(f"{Colors.YELLOW}Note: Restart your terminal/PowerShell to use the 'analyze' command{Colors.RESET}\n")
    
    print(f"Output directory: ~/Desktop/pcap_analysis_output/\n")

def main():
    """Main installation process"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}PCAP Analyzer - Universal Installer{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}\n")
    
    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Install dependencies
    if not install_dependencies():
        print_error("Failed to install dependencies")
        sys.exit(1)
    
    # Step 3: Get installation paths
    tools_dir, output_dir, bin_dir, wrapper_name = get_install_paths()
    
    print(f"\nInstallation paths:")
    print(f"  Tools: {tools_dir}")
    print(f"  Output: {output_dir}")
    print(f"  Command: {bin_dir / wrapper_name}\n")
    
    # Step 4: Copy files
    if not copy_files(tools_dir):
        print_error("Failed to copy files")
        sys.exit(1)
    
    # Step 5: Create output directory
    if not create_output_directory(output_dir):
        print_error("Failed to create output directory")
        sys.exit(1)
    
    # Step 6: Create wrapper
    if not create_wrapper(tools_dir, bin_dir, wrapper_name):
        print_error("Failed to create command wrapper")
        sys.exit(1)
    
    # Step 7: Test installation
    test_installation()
    
    # Step 8: Print usage instructions
    print_usage_instructions()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Installation cancelled{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Installation failed: {e}")
        sys.exit(1)
