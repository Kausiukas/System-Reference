# Function-Level Profiling Guide

This guide explains how to use the profiling utilities in `profiling_utils.py` to measure and analyze the performance of functions and code blocks in your application.

## Available Profiling Tools

### 1. Function Decorator: `@profile_function`
Profiles a function using cProfile. Saves results to a file or prints to stdout.

**Usage:**
```python
from profiling_utils import profile_function

@profile_function(output_file="profiles/my_func_profile.txt")
def my_function(...):
    ...
```
- `output_file` (optional): Path to save the profiling summary. If omitted, prints to stdout.

### 2. Block Context Manager: `profile_block`
Profiles a block of code using cProfile. Saves results to a file or prints to stdout.

**Usage:**
```python
from profiling_utils import profile_block

with profile_block(output_file="profiles/block_profile.txt"):
    ...  # Code to profile
```

### 3. Line-by-Line Profiling: `@line_profile_function`
Profiles a function line-by-line (requires `line_profiler` package).

**Usage:**
```python
from profiling_utils import line_profile_function

@line_profile_function
def my_function(...):
    ...
```

### 4. CLI Script Profiling
Profile an entire script from the command line:
```sh
python profiling_utils.py my_script.py --output profiles/my_script.prof
```
- Use `snakeviz` or `gprof2dot` to visualize `.prof` files.

## Best Practices
- Save profiling results to the `profiles/` directory for easy access and dashboard integration.
- Use profiling selectively (e.g., enable via config or environment variable) to avoid overhead in production.
- Review profiling summaries in the dashboard or with visualization tools.
- Remove or disable profiling decorators/context managers after optimization is complete.

## Dashboard Integration
- The dashboard automatically displays recent profiling summaries from the `profiles/` directory.
- For persistent tracking, consider logging profiling metadata (function name, timestamp, output file) to `metrics_history.json`.

## Example: Profiling a Slow Function
```python
from profiling_utils import profile_function

@profile_function(output_file="profiles/slow_func_profile.txt")
def slow_func(x):
    s = 0
    for i in range(100000):
        s += (i * x) % 7
    return s

slow_func(42)
```

## Enabling/Disabling Profiling
- You can use environment variables or config flags to control profiling. For example:
```python
import os
from profiling_utils import profile_function

if os.getenv("ENABLE_PROFILING") == "1":
    decorator = profile_function(output_file="profiles/my_func_profile.txt")
else:
    decorator = lambda f: f

@decorator
def my_function(...):
    ...
``` 