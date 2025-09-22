#!/usr/bin/env python3
"""
Demo script showing how to use the flaky test detector.
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages for flaky test detection."""
    packages = [
        "pytest",
        "pytest-repeat", 
        "pytest-rerunfailures",
        "requests",
        "psutil"
    ]
    
    print("📦 Installing required packages...")
    for package in packages:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print(f"  ✅ {package}")
        except subprocess.CalledProcessError:
            print(f"  ❌ Failed to install {package}")

def run_flaky_detection():
    """Run the flaky test detection on example tests."""
    print("\n🔍 Running flaky test detection...")
    
    # Check if example test file exists
    if not os.path.exists("example_flaky_tests.py"):
        print("❌ example_flaky_tests.py not found. Please create it first.")
        return
    
    # Run the flaky test detector
    try:
        result = subprocess.run([
            sys.executable, "flaky_test_detector.py",
            "--test-file", "example_flaky_tests.py",
            "--runs", "3",
            "--pattern-analysis",
            "--output", "flaky_test_report.txt"
        ], capture_output=True, text=True)
        
        print("📊 Flaky Test Detection Results:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  Warnings/Errors:")
            print(result.stderr)
            
        if os.path.exists("flaky_test_report.txt"):
            print("\n📄 Detailed report saved to: flaky_test_report.txt")
            
    except Exception as e:
        print(f"❌ Error running flaky test detection: {e}")

def run_manual_flaky_detection():
    """Run manual flaky test detection using pytest-repeat."""
    print("\n🔄 Running manual flaky test detection with pytest-repeat...")
    
    try:
        # Run tests multiple times
        for i in range(1, 4):
            print(f"\n--- Run {i}/3 ---")
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "example_flaky_tests.py", 
                "-v", "--tb=short"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ All tests passed")
            else:
                print("❌ Some tests failed")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                
    except Exception as e:
        print(f"❌ Error in manual detection: {e}")

def main():
    """Main function."""
    print("🚀 Flaky Test Detection Demo")
    print("=" * 40)
    
    # Install requirements
    install_requirements()
    
    # Run automated flaky test detection
    run_flaky_detection()
    
    # Run manual detection
    run_manual_flaky_detection()
    
    print("\n💡 Tips for fixing flaky tests:")
    print("1. Use fixed seeds for random data")
    print("2. Mock external dependencies")
    print("3. Use proper timeouts instead of sleep()")
    print("4. Clean up test state properly")
    print("5. Avoid modifying global state")
    print("6. Use deterministic test data")

if __name__ == "__main__":
    main()
