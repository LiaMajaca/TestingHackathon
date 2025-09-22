#!/usr/bin/env python3
"""
Flaky Test Detector - Extension for testbot.py
Detects and analyzes flaky tests in your codebase.
Usage: python3 flaky_test_detector.py [options]
"""

import os
import re
import subprocess
import time
import json
import argparse
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import glob

class FlakyTestDetector:
    def __init__(self, test_directory: str = "tests", runs: int = 5):
        self.test_directory = test_directory
        self.runs = runs
        self.flaky_tests = []
        self.test_results = defaultdict(list)
        
    def run_test_multiple_times(self, test_file: str = None) -> Dict[str, List[bool]]:
        """Run tests multiple times to detect flakiness."""
        print(f"🔄 Running tests {self.runs} times to detect flakiness...")
        
        test_command = self._build_test_command(test_file)
        results = defaultdict(list)
        
        for run in range(1, self.runs + 1):
            print(f"  Run {run}/{self.runs}...")
            start_time = time.time()
            
            try:
                result = subprocess.run(
                    test_command,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                duration = time.time() - start_time
                success = result.returncode == 0
                
                # Parse test results
                test_names = self._parse_test_output(result.stdout, result.stderr)
                
                for test_name in test_names:
                    results[test_name].append({
                        'success': success,
                        'duration': duration,
                        'run': run,
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    })
                    
            except subprocess.TimeoutExpired:
                print(f"    ⏰ Run {run} timed out")
                for test_name in results.keys():
                    results[test_name].append({
                        'success': False,
                        'duration': 300,
                        'run': run,
                        'stdout': '',
                        'stderr': 'Test execution timed out'
                    })
            except Exception as e:
                print(f"    ❌ Run {run} failed: {e}")
                
        return results
    
    def _build_test_command(self, test_file: str = None) -> List[str]:
        """Build the test command based on available test frameworks."""
        if test_file:
            return ["python", "-m", "pytest", test_file, "-v"]
        else:
            return ["python", "-m", "pytest", self.test_directory, "-v"]
    
    def _parse_test_output(self, stdout: str, stderr: str) -> List[str]:
        """Parse test output to extract test names."""
        test_names = []
        
        # Look for pytest output patterns
        pytest_patterns = [
            r'::(\w+)::(\w+)',
            r'(\w+)\.py::(\w+)',
            r'(\w+)\.py::(\w+)::(\w+)'
        ]
        
        for pattern in pytest_patterns:
            matches = re.findall(pattern, stdout)
            for match in matches:
                if len(match) == 2:
                    test_names.append(f"{match[0]}::{match[1]}")
                elif len(match) == 3:
                    test_names.append(f"{match[0]}::{match[1]}::{match[2]}")
        
        # If no specific tests found, return a generic identifier
        if not test_names:
            test_names = ["all_tests"]
            
        return test_names
    
    def analyze_flakiness(self, results: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """Analyze test results to identify flaky tests."""
        flaky_analysis = {}
        
        for test_name, runs in results.items():
            if not runs:
                continue
                
            successes = [run['success'] for run in runs]
            durations = [run['duration'] for run in runs]
            
            success_rate = sum(successes) / len(successes)
            avg_duration = sum(durations) / len(durations)
            duration_variance = self._calculate_variance(durations)
            
            # Determine flakiness level
            if success_rate < 1.0 and success_rate > 0.0:
                flakiness_level = "FLAKY"
            elif success_rate == 0.0:
                flakiness_level = "FAILING"
            else:
                flakiness_level = "STABLE"
            
            # Check for performance flakiness (high duration variance)
            if duration_variance > avg_duration * 0.5:  # 50% variance threshold
                flakiness_level += "_PERFORMANCE"
            
            flaky_analysis[test_name] = {
                'flakiness_level': flakiness_level,
                'success_rate': success_rate,
                'total_runs': len(runs),
                'successful_runs': sum(successes),
                'failed_runs': len(successes) - sum(successes),
                'avg_duration': avg_duration,
                'duration_variance': duration_variance,
                'runs': runs
            }
            
        return flaky_analysis
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values."""
        if len(values) < 2:
            return 0.0
            
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def detect_flaky_patterns(self, test_file_path: str) -> List[Dict]:
        """Detect common flaky test patterns in code."""
        flaky_patterns = []
        
        try:
            with open(test_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Pattern 1: Time-dependent tests
            time_patterns = [
                r'time\.sleep\(',
                r'asyncio\.sleep\(',
                r'threading\.Event\(\)\.wait\(',
                r'\.join\(timeout=',
                r'wait_for\('
            ]
            
            for pattern in time_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    flaky_patterns.append({
                        'type': 'TIME_DEPENDENT',
                        'pattern': pattern,
                        'line': content[:match.start()].count('\n') + 1,
                        'description': 'Test depends on timing which can be unreliable'
                    })
            
            # Pattern 2: Random data usage
            random_patterns = [
                r'random\.',
                r'numpy\.random\.',
                r'uuid\.uuid4\(\)',
                r'\.shuffle\(',
                r'\.choice\('
            ]
            
            for pattern in random_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    flaky_patterns.append({
                        'type': 'RANDOM_DATA',
                        'pattern': pattern,
                        'line': content[:match.start()].count('\n') + 1,
                        'description': 'Test uses random data without fixed seed'
                    })
            
            # Pattern 3: External dependencies
            external_patterns = [
                r'requests\.',
                r'urllib\.',
                r'http\.',
                r'socket\.',
                r'subprocess\.',
                r'os\.system\(',
                r'os\.popen\('
            ]
            
            for pattern in external_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    flaky_patterns.append({
                        'type': 'EXTERNAL_DEPENDENCY',
                        'pattern': pattern,
                        'line': content[:match.start()].count('\n') + 1,
                        'description': 'Test depends on external resources'
                    })
            
            # Pattern 4: File system operations
            filesystem_patterns = [
                r'open\(',
                r'\.write\(',
                r'\.read\(',
                r'os\.remove\(',
                r'os\.mkdir\(',
                r'shutil\.'
            ]
            
            for pattern in filesystem_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    flaky_patterns.append({
                        'type': 'FILESYSTEM',
                        'pattern': pattern,
                        'line': content[:match.start()].count('\n') + 1,
                        'description': 'Test performs file system operations'
                    })
            
            # Pattern 5: Global state modifications
            global_patterns = [
                r'global\s+\w+',
                r'os\.environ\[',
                r'sys\.path\.',
                r'__import__\('
            ]
            
            for pattern in global_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    flaky_patterns.append({
                        'type': 'GLOBAL_STATE',
                        'pattern': pattern,
                        'line': content[:match.start()].count('\n') + 1,
                        'description': 'Test modifies global state'
                    })
                    
        except Exception as e:
            print(f"Error analyzing {test_file_path}: {e}")
            
        return flaky_patterns
    
    def generate_flaky_test_report(self, analysis: Dict[str, Dict], pattern_analysis: Dict[str, List[Dict]]) -> str:
        """Generate a comprehensive flaky test report."""
        report = []
        report.append("🔍 FLAKY TEST ANALYSIS REPORT")
        report.append("=" * 50)
        report.append("")
        
        # Summary statistics
        total_tests = len(analysis)
        flaky_tests = [name for name, data in analysis.items() if 'FLAKY' in data['flakiness_level']]
        failing_tests = [name for name, data in analysis.items() if data['flakiness_level'] == 'FAILING']
        stable_tests = [name for name, data in analysis.items() if data['flakiness_level'] == 'STABLE']
        
        report.append("📊 SUMMARY:")
        report.append(f"- Total tests analyzed: {total_tests}")
        report.append(f"- Flaky tests: {len(flaky_tests)}")
        report.append(f"- Failing tests: {len(failing_tests)}")
        report.append(f"- Stable tests: {len(stable_tests)}")
        report.append("")
        
        # Flaky tests details
        if flaky_tests:
            report.append("🚨 FLAKY TESTS DETECTED:")
            report.append("-" * 30)
            
            for test_name in flaky_tests:
                data = analysis[test_name]
                report.append(f"• {test_name}")
                report.append(f"  Success rate: {data['success_rate']:.1%}")
                report.append(f"  Runs: {data['successful_runs']}/{data['total_runs']} passed")
                report.append(f"  Avg duration: {data['avg_duration']:.2f}s")
                if data['duration_variance'] > 0:
                    report.append(f"  Duration variance: {data['duration_variance']:.2f}s")
                report.append("")
        
        # Failing tests
        if failing_tests:
            report.append("❌ FAILING TESTS:")
            report.append("-" * 20)
            for test_name in failing_tests:
                report.append(f"• {test_name}")
            report.append("")
        
        # Pattern analysis
        if pattern_analysis:
            report.append("🔍 FLAKY PATTERNS DETECTED:")
            report.append("-" * 30)
            
            pattern_counts = Counter()
            for file_path, patterns in pattern_analysis.items():
                for pattern in patterns:
                    pattern_counts[pattern['type']] += 1
            
            for pattern_type, count in pattern_counts.most_common():
                report.append(f"• {pattern_type}: {count} occurrences")
            
            report.append("")
            
            # Detailed pattern analysis
            for file_path, patterns in pattern_analysis.items():
                if patterns:
                    report.append(f"📁 {os.path.basename(file_path)}:")
                    for pattern in patterns[:5]:  # Show first 5 patterns
                        report.append(f"  Line {pattern['line']}: {pattern['description']}")
                    if len(patterns) > 5:
                        report.append(f"  ... and {len(patterns) - 5} more patterns")
                    report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS:")
        report.append("-" * 20)
        
        if flaky_tests:
            report.append("1. Fix flaky tests by addressing root causes:")
            for test_name in flaky_tests[:3]:  # Top 3 flaky tests
                report.append(f"   - {test_name}")
            report.append("")
        
        if pattern_counts:
            report.append("2. Common flaky patterns to address:")
            for pattern_type, count in pattern_counts.most_common(3):
                if pattern_type == 'TIME_DEPENDENT':
                    report.append("   - Use proper timeouts and waits instead of sleep()")
                elif pattern_type == 'RANDOM_DATA':
                    report.append("   - Use fixed seeds or mock data for reproducible tests")
                elif pattern_type == 'EXTERNAL_DEPENDENCY':
                    report.append("   - Mock external dependencies and APIs")
                elif pattern_type == 'FILESYSTEM':
                    report.append("   - Use temporary directories and clean up properly")
                elif pattern_type == 'GLOBAL_STATE':
                    report.append("   - Avoid modifying global state in tests")
            report.append("")
        
        report.append("3. Best practices:")
        report.append("   - Use deterministic test data")
        report.append("   - Mock external dependencies")
        report.append("   - Clean up test state between runs")
        report.append("   - Use proper assertions with timeouts")
        report.append("   - Run tests in isolated environments")
        
        return "\n".join(report)
    
    def scan_test_files(self) -> List[str]:
        """Find all test files in the project."""
        test_files = []
        
        # Common test file patterns
        patterns = [
            "**/test_*.py",
            "**/*_test.py",
            "**/tests/**/*.py",
            "**/test/**/*.py"
        ]
        
        for pattern in patterns:
            test_files.extend(glob.glob(pattern, recursive=True))
        
        # Filter out common non-test directories
        exclude_dirs = {'node_modules', '.git', '__pycache__', '.venv', 'venv', 'env'}
        filtered_files = []
        
        for file_path in test_files:
            if not any(exclude_dir in file_path for exclude_dir in exclude_dirs):
                filtered_files.append(file_path)
        
        return filtered_files

def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(description='Detect flaky tests in your codebase')
    parser.add_argument('--test-dir', default='tests',
                       help='Directory containing test files (default: tests)')
    parser.add_argument('--runs', type=int, default=5,
                       help='Number of test runs to perform (default: 5)')
    parser.add_argument('--test-file', 
                       help='Specific test file to analyze')
    parser.add_argument('--pattern-analysis', action='store_true',
                       help='Analyze test files for flaky patterns')
    parser.add_argument('--output', 
                       help='Output file for the report')
    
    args = parser.parse_args()
    
    detector = FlakyTestDetector(test_directory=args.test_dir, runs=args.runs)
    
    # Run flaky test detection
    print("🔍 Starting flaky test detection...")
    results = detector.run_test_multiple_times(args.test_file)
    
    if not results:
        print("❌ No test results found. Make sure you have tests and pytest is installed.")
        return
    
    # Analyze results
    analysis = detector.analyze_flakiness(results)
    
    # Pattern analysis if requested
    pattern_analysis = {}
    if args.pattern_analysis:
        print("🔍 Analyzing test files for flaky patterns...")
        test_files = detector.scan_test_files()
        for test_file in test_files:
            patterns = detector.detect_flaky_patterns(test_file)
            if patterns:
                pattern_analysis[test_file] = patterns
    
    # Generate report
    report = detector.generate_flaky_test_report(analysis, pattern_analysis)
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"📄 Report saved to {args.output}")
    else:
        print(report)

if __name__ == "__main__":
    main()
