"""
SSH Client Module
Reusable SSH connection handler for remote server operations
"""

import paramiko
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class SSHClient:
    """Handles SSH connections and command execution on remote servers"""
    
    def __init__(self, host: str, user: str, key_file: Optional[str] = None, 
                 password: Optional[str] = None, timeout: int = 10):
        """
        Initialize SSH client
        
        Args:
            host: Server hostname or IP
            user: SSH username
            key_file: Path to SSH private key (optional)
            password: SSH password (optional)
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.user = user
        self.key_file = key_file
        self.password = password
        self.timeout = timeout
        self.client = None
        
    def connect(self) -> bool:
        """
        Establish SSH connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.key_file:
                logger.info(f"Connecting to {self.host} with key file")
                self.client.connect(
                    hostname=self.host,
                    username=self.user,
                    key_filename=self.key_file,
                    timeout=self.timeout,
                    banner_timeout=self.timeout
                )
            elif self.password:
                logger.info(f"Connecting to {self.host} with password")
                self.client.connect(
                    hostname=self.host,
                    username=self.user,
                    password=self.password,
                    timeout=self.timeout,
                    banner_timeout=self.timeout
                )
            else:
                logger.error("No authentication method provided (key_file or password)")
                return False
                
            logger.info(f"Successfully connected to {self.host}")
            return True
            
        except paramiko.AuthenticationException:
            logger.error(f"Authentication failed for {self.host}")
            return False
        except paramiko.SSHException as e:
            logger.error(f"SSH error connecting to {self.host}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error connecting to {self.host}: {e}")
            return False
    
    def execute_command(self, command: str) -> Tuple[bool, str, str]:
        """
        Execute command on remote server
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        if not self.client:
            logger.error("Not connected to server")
            return False, "", "Not connected"
        
        try:
            logger.debug(f"Executing command on {self.host}: {command}")
            stdin, stdout, stderr = self.client.exec_command(command)
            
            stdout_text = stdout.read().decode('utf-8').strip()
            stderr_text = stderr.read().decode('utf-8').strip()
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                logger.debug(f"Command executed successfully on {self.host}")
                return True, stdout_text, stderr_text
            else:
                logger.warning(f"Command failed on {self.host} with exit status {exit_status}")
                return False, stdout_text, stderr_text
                
        except Exception as e:
            logger.error(f"Error executing command on {self.host}: {e}")
            return False, "", str(e)
    
    def disconnect(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
            logger.info(f"Disconnected from {self.host}")
            self.client = None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()