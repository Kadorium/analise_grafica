import os
import json
import datetime
import sys

try:
    # Get paths
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(script_dir, 'optimization_requests.log')
    backup_folder = os.path.join(script_dir, 'results', 'optimization')
    
    # Check if log file exists
    if not os.path.exists(log_path):
        print('optimization_requests.log file not found!')
        sys.exit(1)
    
    # Create backup folder if needed
    if not os.path.exists(backup_folder):
        print('Creating backup folder...')
        os.makedirs(backup_folder, exist_ok=True)
    
    # Read log file content
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find position of last JSON object
    last_open_brace_pos = content.rfind('{')
    
    if last_open_brace_pos == -1:
        print('No JSON objects found in the log file!')
        sys.exit(1)
    
    # Extract the last JSON entry
    last_entry = content[last_open_brace_pos:]
    
    # Check if it's a complete JSON object
    try:
        json.loads(last_entry)
        is_valid_json = True
    except json.JSONDecodeError:
        is_valid_json = False
        print('Warning: The last entry is not a complete JSON object!')
    
    # Create timestamp for backup filename
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'optimization_requests_backup_{timestamp}.log'
    backup_path = os.path.join(backup_folder, backup_filename)
    
    # Create backup of original file
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Clear the log file
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write('') # Write an empty string to clear the file
    
    print(f'Log file cleaned successfully. Backup saved as {backup_path}')

except Exception as e:
    print(f'Error: {str(e)}')
    sys.exit(1) 