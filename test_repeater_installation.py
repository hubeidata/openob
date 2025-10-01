#!/usr/bin/env python3
"""
OpenOB Repeater - Test Script
Verifica que todos los componentes estén instalados correctamente
"""

import sys
import subprocess

def test_color(text, color_code):
    """Print colored text"""
    print(f"\033[{color_code}m{text}\033[0m")

def test_ok(msg):
    test_color(f"✓ {msg}", "92")  # Green

def test_fail(msg):
    test_color(f"✗ {msg}", "91")  # Red

def test_warning(msg):
    test_color(f"⚠ {msg}", "93")  # Yellow

def check_python_module(module_name, import_name=None):
    """Check if a Python module is available"""
    if import_name is None:
        import_name = module_name
    
    try:
        __import__(import_name)
        test_ok(f"Python module '{module_name}' is installed")
        return True
    except ImportError:
        test_fail(f"Python module '{module_name}' is NOT installed")
        return False

def check_command(command):
    """Check if a command is available"""
    try:
        subprocess.run([command, '--version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL,
                      timeout=5)
        test_ok(f"Command '{command}' is available")
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        test_fail(f"Command '{command}' is NOT available")
        return False

def check_redis_connection(host='localhost', port=6379):
    """Check Redis connection"""
    try:
        import redis
        r = redis.StrictRedis(host=host, port=port, socket_connect_timeout=2)
        r.ping()
        test_ok(f"Redis is running on {host}:{port}")
        return True
    except Exception as e:
        test_fail(f"Redis is NOT accessible on {host}:{port}: {e}")
        return False

def check_gstreamer_plugins():
    """Check if required GStreamer plugins are available"""
    try:
        import gi
        gi.require_version('Gst', '1.0')
        from gi.repository import Gst
        Gst.init(None)
        
        required_elements = [
            'udpsrc',
            'udpsink',
            'rtpjitterbuffer',
            'appsink',
            'alsasrc',
            'alsasink'
        ]
        
        all_ok = True
        for element in required_elements:
            factory = Gst.ElementFactory.find(element)
            if factory:
                test_ok(f"GStreamer element '{element}' is available")
            else:
                test_fail(f"GStreamer element '{element}' is NOT available")
                all_ok = False
        
        return all_ok
    except Exception as e:
        test_fail(f"Error checking GStreamer: {e}")
        return False

def main():
    print("=" * 60)
    print("OpenOB Repeater - Installation Test")
    print("=" * 60)
    print()
    
    all_tests_passed = True
    
    # Check Python version
    print("Testing Python environment...")
    if sys.version_info >= (3, 6):
        test_ok(f"Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    else:
        test_fail(f"Python version {sys.version_info.major}.{sys.version_info.minor} is too old (need 3.6+)")
        all_tests_passed = False
    print()
    
    # Check required Python modules
    print("Testing Python modules...")
    modules = [
        ('gi', 'gi'),
        ('redis', 'redis'),
        ('argparse', 'argparse')
    ]
    
    for module, import_name in modules:
        if not check_python_module(module, import_name):
            all_tests_passed = False
    print()
    
    # Check GStreamer
    print("Testing GStreamer...")
    if not check_gstreamer_plugins():
        all_tests_passed = False
    print()
    
    # Check system commands
    print("Testing system commands...")
    commands = ['gst-launch-1.0', 'redis-cli']
    for cmd in commands:
        if not check_command(cmd):
            all_tests_passed = False
    print()
    
    # Check Redis
    print("Testing Redis connection...")
    if not check_redis_connection():
        test_warning("Redis is not running or not accessible")
        test_warning("If you're setting up a remote repeater, this is OK")
        # Don't fail the test for Redis
    print()
    
    # Check OpenOB modules
    print("Testing OpenOB modules...")
    try:
        from openob.rtp.repeater import RTPRepeater
        test_ok("OpenOB repeater module is available")
    except ImportError as e:
        test_fail(f"OpenOB repeater module is NOT available: {e}")
        all_tests_passed = False
    
    try:
        from openob.node import Node
        test_ok("OpenOB node module is available")
    except ImportError as e:
        test_fail(f"OpenOB node module is NOT available: {e}")
        all_tests_passed = False
    print()
    
    # Summary
    print("=" * 60)
    if all_tests_passed:
        test_ok("All tests passed! OpenOB Repeater is ready to use.")
        print()
        print("Next steps:")
        print("1. Start Redis (if not already running):")
        print("   sudo systemctl start redis-server")
        print()
        print("2. Start the repeater:")
        print("   openob <config_host> repeater transmission repeater")
        print()
    else:
        test_fail("Some tests failed. Please install missing dependencies.")
        print()
        print("Installation commands:")
        print()
        print("Debian/Ubuntu:")
        print("  sudo apt-get install redis-server python3-gi \\")
        print("    gir1.2-gstreamer-1.0 gstreamer1.0-plugins-base \\")
        print("    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \\")
        print("    gstreamer1.0-plugins-ugly python3-redis")
        print()
        print("OpenOB installation:")
        print("  sudo pip3 install -e /path/to/openob")
        print()
    print("=" * 60)
    
    return 0 if all_tests_passed else 1

if __name__ == '__main__':
    sys.exit(main())
