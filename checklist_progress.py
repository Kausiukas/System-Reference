import re
from datetime import datetime

def count_tasks(content):
    """Count total and completed tasks in the checklist."""
    # Count all tasks (lines with checkboxes)
    total_tasks = len(re.findall(r'- \[[ x]\]', content))
    
    # Count completed tasks (lines with checked boxes)
    completed_tasks = len(re.findall(r'- \[x\]', content))
    
    return total_tasks, completed_tasks

def update_progress(file_path):
    """Update the progress tracking section in the checklist file."""
    # Read the current content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count tasks
    total, completed = count_tasks(content)
    
    # Calculate percentage
    percentage = (completed / total * 100) if total > 0 else 0
    
    # Create new progress section
    progress_section = f"""## Progress Tracking
- Total Tasks: [{total}]
- Completed Tasks: [{completed}]
- Completion Percentage: [{percentage:.1f}]%

Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    # Replace the progress section
    new_content = re.sub(
        r'## Progress Tracking.*?Last Updated:.*?\n',
        progress_section,
        content,
        flags=re.DOTALL
    )
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return total, completed, percentage

def main():
    checklist_file = 'memory_optimization_checklist.md'
    try:
        total, completed, percentage = update_progress(checklist_file)
        print(f"Progress updated successfully!")
        print(f"Total Tasks: {total}")
        print(f"Completed Tasks: {completed}")
        print(f"Completion Percentage: {percentage:.1f}%")
    except Exception as e:
        print(f"Error updating progress: {str(e)}")

if __name__ == "__main__":
    main() 