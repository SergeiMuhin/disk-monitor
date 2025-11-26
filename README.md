# Disk Monitor

A production-ready Python tool for monitoring disk usage on remote servers via SSH, with configurable alerting through Email and Slack.

## Features

✅ **SSH-based monitoring** - Connect to remote servers securely  
✅ **Configurable thresholds** - Set custom disk usage alerts  
✅ **Multiple alert channels** - Email (SMTP) and Slack webhooks  
✅ **Retry logic** - Automatic retry on connection failures  
✅ **Comprehensive logging** - File and console logging  
✅ **Modular design** - Reusable components for other projects  
✅ **Error handling** - Graceful failure handling  

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd disk-monitor
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

Or using virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure
```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your servers and alert settings
```

## Configuration

Edit `config.yaml`:
```yaml
servers:
  - host: "192.168.1.10"
    user: "admin"
    key_file: "~/.ssh/id_rsa"

threshold: 80

alerts:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    sender: "alerts@example.com"
    password: "your_app_password"
    recipients:
      - "admin@example.com"
  
  slack:
    enabled: true
    webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    channel: "#alerts"
```

## Usage

### Basic usage
```bash
python disk_monitor.py
```

### With custom config
```bash
python disk_monitor.py --config my_config.yaml
```

### Verbose mode
```bash
python disk_monitor.py --verbose
```

### Schedule with cron
```bash
# Edit crontab
crontab -e

# Run every hour
0 * * * * cd /path/to/disk-monitor && /usr/bin/python3 disk_monitor.py >> /var/log/disk_monitor_cron.log 2>&1
```

## Reusable Components

The `lib/` directory contains reusable modules:

### SSH Client (`lib/ssh_client.py`)
```python
from lib.ssh_client import SSHClient

with SSHClient('192.168.1.10', 'admin', key_file='~/.ssh/id_rsa') as ssh:
    success, stdout, stderr = ssh.execute_command('uptime')
    print(stdout)
```

### Alert Manager (`lib/alerts.py`)
```python
from lib.alerts import SimpleSlackAlert

SimpleSlackAlert.send(
    webhook_url='https://hooks.slack.com/...',
    message='Server is down!',
    channel='#ops'
)
```

### Disk Checker (`lib/disk_checker.py`)
```python
from lib.disk_checker import DiskChecker

df_output = "..."  # from df -h command
disk_usages = DiskChecker.parse_df_output(df_output)
exceeding = DiskChecker.check_threshold(disk_usages, threshold=80)
```

## Testing
```bash
python -m unittest tests/test_disk_monitor.py
```

Or with verbose output:
```bash
python -m unittest tests/test_disk_monitor.py -v
```

## Logging

Logs are written to:
- **Console** - INFO level and above
- **disk_monitor.log** - All levels

## Troubleshooting

### SSH Connection Issues

1. Verify SSH key permissions: `chmod 600 ~/.ssh/id_rsa`
2. Test manual SSH: `ssh user@host`
3. Check firewall rules on remote server

### Slack Webhook Issues

1. Verify webhook URL is correct
2. Test with curl:
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test message"}' \
  YOUR_WEBHOOK_URL
```

### Email Issues

1. For Gmail, use App Password (not regular password)
2. Enable "Less secure app access" or use OAuth2
3. Check SMTP server and port

## Security Best Practices

- ✅ Use SSH keys instead of passwords
- ✅ Store sensitive configs outside repository
- ✅ Use environment variables for credentials
- ✅ Restrict SSH key file permissions (600)
- ✅ Keep dependencies updated

## License

MIT

## Author

DevOps Engineer