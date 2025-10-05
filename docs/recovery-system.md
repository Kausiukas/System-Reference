# Process Recovery System Documentation

## Overview

The Process Recovery System provides automated monitoring, recovery, and task continuation for complex operations that may timeout or lose connection. It consists of two main components:

1. **Cursor IDE Rules** - Immediate recovery rules that activate when Cursor detects issues
2. **Process Recovery Agent** - A specialized background agent that runs alongside your main operations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cursor IDE Rules                        │
├─────────────────────────────────────────────────────────────┤
│  • Process timeout detection                               │
│  • Connection loss handling                                │
│  • Immediate recovery actions                              │
│  • Tasklog.md updates                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Process Recovery Agent                      │
├─────────────────────────────────────────────────────────────┤
│  • Background monitoring                                   │
│  • Task state management                                   │
│  • Intelligent task recommendation                         │
│  • Automated task execution                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Task Management                         │
├─────────────────────────────────────────────────────────────┤
│  • tasklog.md - Progress tracking                          │
│  • shared_state.json - State persistence                   │
│  • recovery_state.json - Recovery metadata                 │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Quick Setup
```bash
# Run the installation script
sudo /workspace/scripts/install_recovery_system.sh
```

### Manual Setup
```bash
# Install dependencies
pip install psutil pyyaml requests

# Start the recovery agent
/workspace/scripts/start_recovery_agent.sh
```

## Configuration

### Cursor IDE Rules (`.cursorrules`)
The Cursor IDE rules are automatically loaded and provide:
- Process timeout detection
- Connection loss handling
- Automatic tasklog updates
- Task recommendation

### Recovery Agent Config (`config/recovery_config.yaml`)
```yaml
# Process monitoring settings
process_timeout: 300  # 5 minutes
memory_threshold: 0.8  # 80%
check_interval: 30  # 30 seconds

# Task priorities
task_priorities:
  critical: ["setup", "initialization", "deployment"]
  high: ["analysis", "testing", "integration"]
  medium: ["documentation", "optimization"]
  low: ["cleanup", "maintenance"]
```

## Usage

### Automatic Operation
The system runs automatically once installed. It will:
1. Monitor your processes for timeouts and failures
2. Update `tasklog.md` with progress and status
3. Recommend next tasks based on current state
4. Automatically execute recommended tasks

### Manual Control
```bash
# Check status
systemctl status recovery-agent

# View logs
tail -f /workspace/recovery_agent.log

# View tasklog
cat /workspace/tasklog.md

# Manual recovery trigger
python3 -c "
from src.utils.recovery_integration import RecoveryIntegration
ri = RecoveryIntegration()
ri.trigger_manual_recovery('manual_trigger')
"
```

### Task Management
Tasks are automatically prioritized and executed based on:
- Dependencies
- Criticality level
- Current system state
- Previous task completion

## File Structure

```
/workspace/
├── .cursorrules                          # Cursor IDE rules
├── tasklog.md                           # Progress tracking
├── recovery_state.json                  # Recovery metadata
├── config/
│   ├── recovery_config.yaml            # Agent configuration
│   └── recovery-agent.service          # Systemd service
├── src/recovery/
│   └── process_recovery_agent.py       # Main recovery agent
├── src/utils/
│   └── recovery_integration.py         # Integration utilities
└── scripts/
    ├── start_recovery_agent.sh         # Startup script
    └── install_recovery_system.sh      # Installation script
```

## Monitoring

### Health Checks
The system continuously monitors:
- Process execution time
- Memory usage
- Connection health
- File system access
- Task completion status

### Logs
- **Recovery Agent**: `/workspace/recovery_agent.log`
- **Systemd**: `journalctl -u recovery-agent -f`
- **Task Progress**: `/workspace/tasklog.md`

### Status Indicators
- **Active Tasks**: Currently running tasks
- **Completed Tasks**: Successfully finished tasks
- **Failed Tasks**: Tasks that encountered errors
- **Recovery Count**: Number of recovery attempts

## Troubleshooting

### Common Issues

1. **Agent not starting**
   ```bash
   # Check logs
   journalctl -u recovery-agent -f
   
   # Restart service
   sudo systemctl restart recovery-agent
   ```

2. **Tasks not executing**
   ```bash
   # Check configuration
   cat /workspace/config/recovery_config.yaml
   
   # Check tasklog
   tail -f /workspace/tasklog.md
   ```

3. **Memory issues**
   ```bash
   # Check memory usage
   free -h
   
   # Adjust memory threshold in config
   vim /workspace/config/recovery_config.yaml
   ```

### Manual Recovery
If automatic recovery fails:
```bash
# Trigger manual recovery
python3 -c "
from src.utils.recovery_integration import RecoveryIntegration
ri = RecoveryIntegration()
ri.trigger_manual_recovery('manual_intervention')
"

# Check recommended next task
python3 -c "
from src.utils.recovery_integration import RecoveryIntegration
ri = RecoveryIntegration()
print('Next task:', ri.get_recommended_next_task())
"
```

## Customization

### Adding New Tasks
1. Update `config/recovery_config.yaml` with new task
2. Add task execution logic in `process_recovery_agent.py`
3. Update task priorities as needed

### Modifying Recovery Behavior
1. Edit `.cursorrules` for Cursor IDE behavior
2. Modify `recovery_config.yaml` for agent behavior
3. Update `recovery_integration.py` for custom logic

### Integration with Existing Systems
The recovery system integrates with your existing shared state management:
- Reads from `shared_state.json`
- Updates task progress
- Provides recommendations based on analysis results

## Best Practices

1. **Regular Monitoring**: Check `tasklog.md` regularly for progress
2. **Configuration Tuning**: Adjust timeouts and thresholds based on your workload
3. **Backup State**: The system automatically saves state, but consider additional backups
4. **Log Rotation**: Monitor log file sizes and implement rotation if needed
5. **Testing**: Test recovery scenarios in a safe environment first

## Support

For issues or questions:
1. Check the logs first
2. Review the configuration
3. Test with manual recovery triggers
4. Check system resources (memory, disk space)

The system is designed to be self-healing and should handle most common failure scenarios automatically.