#!/usr/bin/env python3
"""
Disk Monitor - Remote Server Disk Usage Monitor
Monitors disk usage on remote servers and sends alerts when threshold is exceeded
"""

import os
import sys
import yaml
import logging
import argparse
from typing import Dict, List
from pathlib import Path

from lib.ssh_client import SSHClient
from lib.disk_checker import DiskChecker
from lib.alerts import AlertManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('disk_monitor.log')
    ]
)
logger = logging.getLogger(__name__)


class DiskMonitor:
    """Main disk monitoring orchestrator"""
    
    def __init__(self, config_path: str):
        """
        Initialize disk monitor
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.alert_manager = AlertManager(self.config.get('alerts', {}))
        self.threshold = self.config.get('threshold', 80)
        self.ssh_config = self.config.get('ssh', {})
        
    def _load_config(self, config_path: str) -> Dict:
        """Load YAML configuration file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            sys.exit(1)
    
    def check_server(self, server_config: Dict) -> bool:
        """
        Check disk usage on a single server
        
        Args:
            server_config: Server configuration dictionary
            
        Returns:
            bool: True if check successful
        """
        host = server_config['host']
        user = server_config['user']
        key_file = server_config.get('key_file')
        password = server_config.get('password')
        
        logger.info(f"Checking server: {host}")
        
        # Expand home directory in key_file path
        if key_file:
            key_file = os.path.expanduser(key_file)
        
        # Create SSH client with retry logic
        timeout = self.ssh_config.get('timeout', 10)
        retry_attempts = self.ssh_config.get('retry_attempts', 3)
        
        for attempt in range(1, retry_attempts + 1):
            ssh_client = SSHClient(host, user, key_file, password, timeout)
            
            if not ssh_client.connect():
                logger.warning(f"Connection attempt {attempt}/{retry_attempts} failed for {host}")
                if attempt < retry_attempts:
                    continue
                else:
                    logger.error(f"Failed to connect to {host} after {retry_attempts} attempts")
                    self._send_connection_failure_alert(host)
                    return False
            
            # Execute df command
            success, stdout, stderr = ssh_client.execute_command('df -h')
            ssh_client.disconnect()
            
            if not success:
                logger.error(f"Failed to execute df command on {host}: {stderr}")
                return False
            
            # Parse disk usage
            disk_usages = DiskChecker.parse_df_output(stdout)
            
            if not disk_usages:
                logger.warning(f"No disk usage data parsed from {host}")
                return False
            
            # Check threshold
            exceeding = DiskChecker.check_threshold(disk_usages, self.threshold)
            
            if exceeding:
                logger.warning(f"Disk usage threshold exceeded on {host}")
                self._send_disk_alert(host, exceeding)
            else:
                logger.info(f"All disks on {host} are within threshold")
            
            return True
        
        return False
    
    def _send_disk_alert(self, host: str, disk_usages: List):
        """Send alert for disk usage threshold exceeded"""
        subject = f"⚠️ Disk Usage Alert: {host}"
        message = DiskChecker.format_alert_message(host, disk_usages, self.threshold)
        
        logger.info(f"Sending alert for {host}")
        self.alert_manager.send_alert(subject, message, severity='warning')
    
    def _send_connection_failure_alert(self, host: str):
        """Send alert for connection failure"""
        subject = f"🔴 Connection Failed: {host}"
        message = f"Failed to connect to server {host}\nPlease check network connectivity and SSH credentials."
        
        logger.info(f"Sending connection failure alert for {host}")
        self.alert_manager.send_alert(subject, message, severity='critical')
    
    def run(self):
        """Run disk check on all configured servers"""
        servers = self.config.get('servers', [])
        
        if not servers:
            logger.error("No servers configured")
            sys.exit(1)
        
        logger.info(f"Starting disk monitoring for {len(servers)} servers")
        
        success_count = 0
        failure_count = 0
        
        for server in servers:
            if self.check_server(server):
                success_count += 1
            else:
                failure_count += 1
        
        logger.info(f"Monitoring complete: {success_count} successful, {failure_count} failed")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Monitor disk usage on remote servers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config config.yaml
  %(prog)s -c my_config.yaml --verbose
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if config file exists
    if not Path(args.config).exists():
        logger.error(f"Configuration file not found: {args.config}")
        logger.info("Copy config.yaml.example to config.yaml and edit it")
        sys.exit(1)
    
    # Run monitor
    try:
        monitor = DiskMonitor(args.config)
        monitor.run()
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()