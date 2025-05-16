import re
import time
import schedule
import os

CHECKLIST_FILE = 'memory_optimization_checklist.md'

# Helper: get all function definitions in the codebase

def get_all_function_defs():
    func_defs = {}
    for root, dirs, files in os.walk('.'):
        for fname in files:
            if fname.endswith('.py') and not fname.startswith('.'):  # skip hidden/compiled
                path = os.path.join(root, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f, 1):
                            m = re.match(r'\s*def\s+([a-zA-Z0-9_]+)\s*\(', line)
                            if m:
                                func_name = m.group(1)
                                func_defs[func_name] = f"{path[2:] if path.startswith('./') else path}:{i}"
                except Exception:
                    continue
    return func_defs


def get_uncompleted_tasks_with_lines():
    with open(CHECKLIST_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    uncompleted = []
    for idx, line in enumerate(lines):
        # Match lines with unchecked tasks
        if re.search(r'- \[ \]', line):
            uncompleted.append((idx, line.rstrip('\n')))
    return uncompleted, lines


def update_checklist_with_priorities_and_completion():
    func_defs = get_all_function_defs()
    uncompleted, lines = get_uncompleted_tasks_with_lines()
    cleaned = []
    for idx, line in enumerate(lines):
        if re.search(r'- \[ \]', line):
            # Remove any trailing [number] at end
            line = re.sub(r'\s*\[\d+\]$', '', line)
            cleaned.append((idx, line))
        else:
            cleaned.append((idx, line.rstrip('\n')))
    # Assign priorities and check for completion
    priority = 1
    for idx, line in [c for c in cleaned if re.search(r'- \[ \]', c[1])]:
        # Try to extract a function name (e.g., defragment_index, run_stress_test, etc.)
        m = re.search(r'([a-zA-Z0-9_]+)\s*\(', line)
        if not m:
            m = re.search(r'([a-zA-Z0-9_]+)', line)
        func_name = m.group(1) if m else None
        found = func_name and func_name in func_defs
        if found:
            # Mark as complete and add reference
            ref = func_defs[func_name]
            lines[idx] = re.sub(r'- \[ \]', '- [x]', line) + f' (Completed in {ref})\n'
        else:
            # Append [N] at the end
            lines[idx] = f"{line} [{priority}]\n"
            priority += 1
    # Write back to file
    with open(CHECKLIST_FILE, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"Checklist updated: completed tasks marked, priorities assigned to {priority-1} uncompleted tasks.")


def print_uncompleted_tasks_with_priorities():
    uncompleted, _ = get_uncompleted_tasks_with_lines()
    print('Uncompleted Tasks (by priority):')
    for i, (idx, line) in enumerate(uncompleted, 1):
        print(f"{i}. {line} [{i}]")
    if uncompleted:
        print(f"\nSuggested next task: {uncompleted[0][1]} [1]")
    else:
        print("\nAll tasks are complete!")


def run_evaluator():
    print("\n--- Checklist Priority Evaluation ---")
    print_uncompleted_tasks_with_priorities()
    print("--- End Evaluation ---\n")


def autoschedule_evaluator(interval_minutes=10):
    schedule.every(interval_minutes).minutes.do(run_evaluator)
    print(f"Evaluator autoschedule started. Running every {interval_minutes} minutes.")
    run_evaluator()  # Run once at start
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    import sys
    if '--update' in sys.argv:
        update_checklist_with_priorities_and_completion()
    elif '--auto' in sys.argv:
        autoschedule_evaluator()
    else:
        print_uncompleted_tasks_with_priorities() 