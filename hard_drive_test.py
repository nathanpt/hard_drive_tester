#!/usr/bin/env python3
"""
Hard Drive Test Script

This script performs comprehensive testing of a hard drive using multiple tools:
fio, badblocks, ioping, iostat, sysbench, and smartmontools.
Results are aggregated into a single timestamped file.

Usage:
    linux: sudo python3 hard_drive_test.py /dev/sdX
"""

import argparse
import datetime
import os
import subprocess
import sys
import time
import shutil
import signal
import logging
from pathlib import Path


class HardDriveTest:
    """Class to manage hard drive testing using various tools."""

    def __init__(self, device):
        """
        Initialize the test environment.
        
        Args:
            device (str): The device identifier (e.g., /dev/sda)
        """
        self.device = device
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_file = f"hard_drive_test_{self.timestamp}.txt"
        self.logger = self._setup_logging()
        
        # Required tools
        self.required_tools = [
            "fio", "badblocks", "ioping", "iostat", "sysbench", "smartctl"
        ]
        
        # Test status tracking
        self.tests_completed = 0
        self.tests_total = 6  # Number of main tests
        
        # Setup signal handlers for graceful termination
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _setup_logging(self):
        """Configure logging to both file and console."""
        logger = logging.getLogger("HardDriveTest")
        logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(self.results_file)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger

    def _handle_interrupt(self, signum, frame):
        """Handle interrupt signals gracefully."""
        self.logger.warning("\nTest interrupted by user. Cleaning up...")
        self._write_section("Test Interrupted", "The test was interrupted before completion.")
        self._write_section("Test Completed", f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sys.exit(1)

    def _write_to_results(self, content):
        """Write content to the results file."""
        with open(self.results_file, 'a') as f:
            f.write(content + "\n")

    def _write_section(self, title, content):
        """Write a formatted section to the results file."""
        section = f"\n{title}\n{'-' * len(title)}\n{content}\n"
        self._write_to_results(section)
        
    def _run_command(self, command, timeout=None):
        """
        Run a shell command and return its output.
        
        Args:
            command (list): Command to run as a list of arguments
            timeout (int, optional): Timeout in seconds
            
        Returns:
            str: Command output
            
        Raises:
            subprocess.SubprocessError: If command fails
        """
        try:
            self.logger.info(f"Running command: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return result.stdout
        except subprocess.SubprocessError as e:
            self.logger.error(f"Command failed: {' '.join(command)}")
            self.logger.error(f"Error: {str(e)}")
            if hasattr(e, 'stdout') and e.stdout:
                self.logger.error(f"Output: {e.stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                self.logger.error(f"Error output: {e.stderr}")
            raise

    def check_requirements(self):
        """
        Check if all required tools are installed and if running with root privileges.
        
        Returns:
            bool: True if all requirements are met, False otherwise
        """
        self.logger.info("Checking requirements...")
        
        # Check for root privileges
        if os.geteuid() != 0:
            self.logger.error("This script requires root privileges. Please run with sudo.")
            return False
            
        # Check for required tools
        missing_tools = []
        for tool in self.required_tools:
            if not shutil.which(tool):
                missing_tools.append(tool)
                
        if missing_tools:
            self.logger.error(f"Missing required tools: {', '.join(missing_tools)}")
            self.logger.error("Please install them before running this script.")
            return False
            
        # Check if device exists
        if not os.path.exists(self.device):
            self.logger.error(f"Device {self.device} does not exist.")
            return False
            
        # Check if device is mounted
        try:
            mount_output = self._run_command(["mount"])
            if self.device in mount_output:
                self.logger.warning(f"Device {self.device} is currently mounted. Tests may be affected.")
                return self._confirm("Continue anyway?")
        except subprocess.SubprocessError:
            self.logger.warning("Could not check if device is mounted.")
            
        return True

    def _confirm(self, message):
        """
        Ask for user confirmation.
        
        Args:
            message (str): Confirmation message
            
        Returns:
            bool: True if confirmed, False otherwise
        """
        response = input(f"{message} (y/n): ").lower()
        return response == 'y' or response == 'yes'

    def display_warning(self):
        """Display warning message and ask for confirmation."""
        warning = """
WARNING: This script will perform intensive testing on the specified drive.
This may cause:
- Significant drive wear
- Potential data loss
- System performance degradation during testing

It is recommended to:
- Backup any important data before proceeding
- Not use the drive for other purposes during testing
- Ensure the system has stable power

The tests will take a significant amount of time to complete.
"""
        print(warning)
        return self._confirm("Do you want to proceed with the tests?")

    def run_smart_test(self, initial=True):
        """
        Run SMART tests using smartctl.
        
        Args:
            initial (bool): Whether this is the initial or final test
        """
        test_name = "Initial SMART Status" if initial else "Final SMART Status"
        self.logger.info(f"Running {test_name}...")
        
        try:
            smart_output = self._run_command(["smartctl", "-a", self.device])
            self._write_section(test_name, smart_output)
            
            if initial:
                # Check if SMART is enabled
                if "SMART support is: Disabled" in smart_output:
                    self.logger.warning("SMART is disabled on this drive.")
                    try:
                        self._run_command(["smartctl", "-s", "on", self.device])
                        self.logger.info("SMART has been enabled.")
                    except subprocess.SubprocessError:
                        self.logger.error("Failed to enable SMART.")
                
                # Check overall health
                try:
                    health_output = self._run_command(["smartctl", "-H", self.device])
                    if "PASSED" in health_output:
                        self.logger.info("SMART health check: PASSED")
                    else:
                        self.logger.warning("SMART health check: FAILED or UNKNOWN")
                except subprocess.SubprocessError:
                    self.logger.error("Failed to check SMART health status.")
            
            if initial:
                self.tests_completed += 1
                
        except subprocess.SubprocessError:
            self.logger.error(f"Failed to run {test_name}.")

    def run_badblocks_test(self):
        """Run badblocks to scan for bad sectors."""
        self.logger.info("Running badblocks scan (read-only)...")
        
        try:
            # Using read-only mode (-b 4096 for 4K blocks, common in modern drives)
            badblocks_output = self._run_command(
                ["badblocks", "-v", "-b", "4096", "-s", self.device]
            )
            self._write_section("Badblocks Scan", badblocks_output)
            self.tests_completed += 1
        except subprocess.SubprocessError:
            self.logger.error("Failed to run badblocks scan.")

    def run_ioping_test(self):
        """Run ioping to measure I/O latency."""
        self.logger.info("Running I/O latency test with ioping...")
        
        try:
            # Run 100 requests with 1 second interval
            ioping_output = self._run_command(
                ["ioping", "-c", "100", "-i", "1s", self.device]
            )
            self._write_section("I/O Ping Latency", ioping_output)
            self.tests_completed += 1
        except subprocess.SubprocessError:
            self.logger.error("Failed to run ioping test.")

    def run_fio_tests(self):
        """Run fio for various I/O stress tests."""
        self.logger.info("Running FIO stress tests...")
        
        # Create a temporary directory for fio tests
        temp_dir = f"/tmp/fio_test_{self.timestamp}"
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Sequential read test
            self.logger.info("Running sequential read test...")
            seq_read_output = self._run_command([
                "fio", "--name=seq-read", f"--filename={self.device}", 
                "--direct=1", "--rw=read", "--bs=4M", "--size=1G",
                "--numjobs=1", "--runtime=60", "--time_based", "--group_reporting"
            ])
            
            # Random read test
            self.logger.info("Running random read test...")
            rand_read_output = self._run_command([
                "fio", "--name=rand-read", f"--filename={self.device}", 
                "--direct=1", "--rw=randread", "--bs=4k", "--size=1G",
                "--numjobs=4", "--runtime=60", "--time_based", "--group_reporting"
            ])
            
            # Random write test
            self.logger.info("Running random write test...")
            rand_write_output = self._run_command([
                "fio", "--name=rand-write", f"--filename={self.device}", 
                "--direct=1", "--rw=randwrite", "--bs=4k", "--size=1G",
                "--numjobs=4", "--runtime=60", "--time_based", "--group_reporting"
            ])
            
            # Mixed read/write test
            self.logger.info("Running mixed read/write test...")
            mixed_output = self._run_command([
                "fio", "--name=mixed", f"--filename={self.device}", 
                "--direct=1", "--rw=randrw", "--bs=4k", "--size=1G",
                "--numjobs=4", "--runtime=60", "--time_based", "--group_reporting"
            ])
            
            # Combine all outputs
            fio_output = "Sequential Read Test:\n" + seq_read_output + "\n\n"
            fio_output += "Random Read Test:\n" + rand_read_output + "\n\n"
            fio_output += "Random Write Test:\n" + rand_write_output + "\n\n"
            fio_output += "Mixed Read/Write Test:\n" + mixed_output
            
            self._write_section("FIO Stress Test", fio_output)
            self.tests_completed += 1
            
        except subprocess.SubprocessError:
            self.logger.error("Failed to run FIO tests.")
        finally:
            # Clean up
            try:
                os.rmdir(temp_dir)
            except:
                self.logger.warning(f"Could not remove temporary directory {temp_dir}")

    def run_sysbench_test(self):
        """Run sysbench for file I/O benchmarking."""
        self.logger.info("Running sysbench file I/O benchmark...")
        
        # Create a temporary directory for sysbench tests
        temp_dir = f"/tmp/sysbench_test_{self.timestamp}"
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Prepare the test files
            self.logger.info("Preparing sysbench test files...")
            prepare_output = self._run_command([
                "sysbench", "fileio", "--file-total-size=2G", 
                f"--file-test-mode=rndrw", f"--file-block-size=4K",
                f"--file-num=64", f"--file-extra-flags=direct",
                f"--file-fsync-freq=0", f"--file-fsync-all=0",
                f"--file-fsync-end=0", f"--time=10",
                "--threads=4", "prepare"
            ], timeout=300)
            
            # Run the benchmark
            self.logger.info("Running sysbench benchmark...")
            benchmark_output = self._run_command([
                "sysbench", "fileio", "--file-total-size=2G", 
                f"--file-test-mode=rndrw", f"--file-block-size=4K",
                f"--file-num=64", f"--file-extra-flags=direct",
                f"--file-fsync-freq=0", f"--file-fsync-all=0",
                f"--file-fsync-end=0", f"--time=60",
                "--threads=4", "run"
            ], timeout=300)
            
            # Cleanup
            self.logger.info("Cleaning up sysbench test files...")
            cleanup_output = self._run_command([
                "sysbench", "fileio", "--file-total-size=2G", 
                f"--file-test-mode=rndrw", f"--file-block-size=4K",
                f"--file-num=64", "cleanup"
            ])
            
            # Combine outputs
            sysbench_output = "Preparation:\n" + prepare_output + "\n\n"
            sysbench_output += "Benchmark:\n" + benchmark_output + "\n\n"
            sysbench_output += "Cleanup:\n" + cleanup_output
            
            self._write_section("Sysbench File I/O Benchmark", sysbench_output)
            self.tests_completed += 1
            
        except subprocess.SubprocessError:
            self.logger.error("Failed to run sysbench tests.")
        finally:
            # Clean up directory
            try:
                os.rmdir(temp_dir)
            except:
                self.logger.warning(f"Could not remove temporary directory {temp_dir}")

    def run_iostat_monitoring(self):
        """Run iostat to collect I/O statistics."""
        self.logger.info("Collecting I/O statistics with iostat...")
        
        try:
            # Run iostat to collect statistics (every 5 seconds, 5 times)
            iostat_output = self._run_command([
                "iostat", "-x", self.device, "5", "5"
            ])
            self._write_section("I/O Statistics", iostat_output)
            self.tests_completed += 1
        except subprocess.SubprocessError:
            self.logger.error("Failed to run iostat monitoring.")

    def monitor_temperature(self):
        """Monitor drive temperature during tests."""
        try:
            temp_output = self._run_command([
                "smartctl", "-A", self.device, "|", "grep", "Temperature"
            ])
            self.logger.info(f"Current drive temperature: {temp_output.strip()}")
        except subprocess.SubprocessError:
            self.logger.warning("Could not monitor drive temperature.")

    def run_all_tests(self):
        """Run all tests in sequence."""
        # Initialize results file
        self._write_to_results(f"Hard Drive Test Results - {self.timestamp}")
        self._write_to_results("=" * 40)
        self._write_to_results(f"\nDevice: {self.device}")
        self._write_to_results(f"\nTest Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run tests
        self.run_smart_test(initial=True)
        self.run_badblocks_test()
        self.run_ioping_test()
        self.run_fio_tests()
        self.run_sysbench_test()
        self.run_iostat_monitoring()
        
        # Final SMART test
        self.run_smart_test(initial=False)
        
        # Write completion time
        self._write_section("Test Completed", f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.logger.info(f"All tests completed. Results saved to {self.results_file}")


def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(
        description="Comprehensive hard drive testing script"
    )
    parser.add_argument(
        "device", 
        help="Device to test (e.g., /dev/sda)"
    )
    args = parser.parse_args()
    
    tester = HardDriveTest(args.device)
    
    # Check requirements
    if not tester.check_requirements():
        sys.exit(1)
    
    # Display warning and get confirmation
    if not tester.display_warning():
        print("Test aborted by user.")
        sys.exit(0)
    
    # Run all tests
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
