# Hard Drive Testing Tool

A comprehensive Python script for testing hard drive performance and health using multiple industry-standard tools.

## Overview

This tool performs an in-depth assessment of a hard drive's performance and integrity by leveraging a suite of diagnostic and benchmarking tools. It automates the execution of these tools, collects their output, and saves the results into a single, timestamped file for easy analysis.

## Features

- **Complete Testing Suite**: Utilizes six powerful tools to evaluate different aspects of drive performance:
  - **fio**: Stress-tests with various I/O workloads
  - **badblocks**: Scans for bad sectors
  - **ioping**: Measures I/O operation latency
  - **iostat**: Provides I/O device statistics
  - **sysbench**: Benchmarks file I/O performance
  - **smartctl**: Retrieves SMART data for health monitoring

- **Comprehensive Results**: All test outputs are consolidated into a single, timestamped file with clear section headers
- **User-Friendly**: Includes safety warnings and requires confirmation before proceeding
- **Robust Error Handling**: Gracefully handles missing tools, device issues, and test failures
- **Progress Tracking**: Shows test completion status throughout the process
- **Flexible Testing**: Option to skip the time-consuming badblocks test for faster results

## Requirements

- Python 3.6+
- Root/Administrator privileges
- The following tools must be installed:
  - fio
  - badblocks (part of e2fsprogs)
  - ioping
  - sysstat (for iostat)
  - sysbench
  - smartmontools (for smartctl)

### Installation of Required Tools

#### On Linux (Debian/Ubuntu):
```bash
sudo apt-get update
sudo apt-get install fio e2fsprogs ioping sysstat sysbench smartmontools
```

#### On Linux (RHEL/CentOS/Fedora):
```bash
sudo dnf install fio e2fsprogs ioping sysstat sysbench smartmontools
```

#### On macOS (using Homebrew):
```bash
brew install fio ioping sysstat sysbench smartmontools
# Note: badblocks may not be available directly on macOS
```

#### On Windows:
Most of these tools are designed for Unix-like systems. For Windows:
- Use Windows Subsystem for Linux (WSL) to run the script
- Or use native Windows alternatives and modify the script accordingly

## Usage

### Basic Usage

```bash
# On Linux
sudo python hard_drive_test.py /dev/sdX

# On Windows (with WSL)
sudo python3 hard_drive_test.py /dev/sdX

# Skip the time-consuming badblocks test
sudo python hard_drive_test.py /dev/sdX --skip-badblocks
```

Replace `/dev/sdX` with your target drive (e.g., `/dev/sda`, `/dev/nvme0n1`).

### Command Line Options

| Option | Description |
|--------|-------------|
| `--skip-badblocks` | Skip the badblocks test, which significantly reduces test time (from hours to minutes) |

### Important Notes

- **Data Safety**: While the default tests are non-destructive, it's always recommended to backup important data before testing
- **Drive Wear**: Intensive testing can cause additional wear on SSDs
- **System Load**: These tests are resource-intensive and may affect system performance while running
- **Time Requirements**: 
  - Full test suite with badblocks: Can take 20-40 hours for 10TB drives
  - Without badblocks (using `--skip-badblocks`): Approximately 15-20 minutes

## Sample Output

The script generates a timestamped results file with the following structure:

```
Hard Drive Test Results - 20250323_123456
========================================

Device: /dev/sda

Test Started: 2025-03-23 12:34:56

Initial SMART Status
--------------------
[Output from smartctl -a /dev/sda]

Badblocks Scan
--------------
[Output from badblocks -v /dev/sda]
or
[Test skipped by user request]

I/O Ping Latency
----------------
[Output from ioping -c 10 /dev/sda]

FIO Stress Test
---------------
[Output from fio --randwrite and --seqread tests]

Sysbench File I/O Benchmark
---------------------------
[Output from sysbench fileio test]

I/O Statistics
--------------
[Output from iostat /dev/sda]

Final SMART Status
------------------
[Output from smartctl -a /dev/sda]

Test Completed: 2025-03-23 13:45:00
```

## Error Handling

The script includes robust error handling for common issues:
- Missing tools
- Insufficient permissions
- Device not found
- Device in use/mounted
- Test failures

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is provided as-is without any warranty. Use at your own risk. The author is not responsible for any data loss or hardware damage that may occur from using this tool.