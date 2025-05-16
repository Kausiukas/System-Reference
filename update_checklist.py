import unittest
import sys
import re
from datetime import datetime
import subprocess
from typing import Tuple, List

def run_tests() -> Tuple[bool, List[str]]:
    """
    Run all test files and return test results.
    
    Returns:
        Tuple of (success: bool, output: List[str])
    """
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = '.'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Capture test output
    test_output = []
    success = True
    
    class TestResult(unittest.TextTestResult):
        def addSuccess(self, test):
            super().addSuccess(test)
            test_output.append(f"✓ {test}")
            
        def addFailure(self, test, err):
            super().addFailure(test, err)
            test_output.append(f"✗ {test}")
            test_output.append(f"  Error: {err[1]}")
            nonlocal success
            success = False
            
        def addError(self, test, err):
            super().addError(test, err)
            test_output.append(f"✗ {test}")
            test_output.append(f"  Error: {err[1]}")
            nonlocal success
            success = False
    
    runner = unittest.TextTestRunner(resultclass=TestResult)
    runner.run(suite)
    
    return success, test_output

def update_checklist(tasks_to_mark: List[str]) -> None:
    """
    Update the checklist file with completed tasks.
    
    Args:
        tasks_to_mark: List of task descriptions to mark as completed
    """
    with open('memory_optimization_checklist.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update each task
    for task in tasks_to_mark:
        # Escape special characters in the task description
        escaped_task = re.escape(task)
        # Replace unchecked box with checked box
        pattern = f"- \\[ \\] {escaped_task}"
        replacement = f"- [x] {task}"
        content = re.sub(pattern, replacement, content)
    
    # Write back to file
    with open('memory_optimization_checklist.md', 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    print("Running tests...")
    success, test_output = run_tests()
    
    # Print test results
    print("\nTest Results:")
    for line in test_output:
        print(line)
    
    if not success:
        print("\n❌ Tests failed. Checklist will not be updated.")
        sys.exit(1)
    
    print("\n✅ All tests passed!")
    
    # Get tasks to mark as completed
    tasks_to_mark = [
        "Replace full collection loading with `get_stats()`",
        "Implement `count()` method for document counting",
        "Add memory usage monitoring with `psutil`",
        "Set up basic memory thresholds",
        "Implement memory usage alerts",
        "Add memory usage logging"
    ]
    
    # Update checklist
    update_checklist(tasks_to_mark)
    print("\nChecklist updated successfully!")
    
    # Run progress calculator
    subprocess.run(['python', 'checklist_progress.py'])

if __name__ == '__main__':
    main() 