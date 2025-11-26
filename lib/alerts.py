"""
Alert Module
Reusable alert handlers for various notification channels
"""

import smtplib
import requests
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages multiple alert channels (Email, Slack, etc.)"""
    
    def __init__(self, config: Dict):
        """
        Initialize alert manager with configuration
        
        Args:
            config: Alert configuration dictionary
        """
        self.config = config
        self.email_config = config.get('email', {})
        self.slack_config = config.get('slack', {})
    
    def send_alert(self, subject: str, message: str, severity: str = "warning"):
        """
        Send alert through all enabled channels
        
        Args:
            subject: Alert subject/title
            message: Alert message body
            severity: Alert severity level (info, warning, critical)
        """
        success = True
        
        if self.email_config.get('enabled', False):
            if not self._send_email(subject, message):
                success = False
        
        if self.slack_config.get('enabled', False):
            if not self._send_slack(subject, message, severity):
                success = False
        
        return success
    
    def _send_email(self, subject: str, message: str) -> bool:
        """
        Send email alert
        
        Args:
            subject: Email subject
            message: Email body
            
        Returns:
            bool: True if successful
        """
        try:
            smtp_server = self.email_config['smtp_server']
            smtp_port = self.email_config['smtp_port']
            sender = self.email_config['sender']
            password = self.email_config['password']
            recipients = self.email_config['recipients']
            
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            logger.info(f"Sending email alert to {len(recipients)} recipients")
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)
            
            logger.info("Email alert sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    def _send_slack(self, subject: str, message: str, severity: str) -> bool:
        """
        Send Slack webhook alert
        
        Args:
            subject: Alert title
            message: Alert message
            severity: Alert severity
            
        Returns:
            bool: True if successful
        """
        try:
            webhook_url = self.slack_config['webhook_url']
            channel = self.slack_config.get('channel', '#alerts')
            
            # Color coding based on severity
            color_map = {
                'info': '#36a64f',      # green
                'warning': '#ff9900',   # orange
                'critical': '#ff0000'   # red
            }
            color = color_map.get(severity, '#ff9900')
            
            payload = {
                'channel': channel,
                'username': 'Disk Monitor',
                'icon_emoji': ':warning:',
                'attachments': [{
                    'color': color,
                    'title': subject,
                    'text': message,
                    'footer': 'Disk Monitoring System',
                    'ts': int(__import__('time').time())
                }]
            }
            
            logger.info(f"Sending Slack alert to {channel}")
            
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Slack alert sent successfully")
                return True
            else:
                logger.error(f"Slack alert failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False


class SimpleEmailAlert:
    """Standalone email alert utility"""
    
    @staticmethod
    def send(smtp_server: str, smtp_port: int, sender: str, password: str,
             recipients: List[str], subject: str, message: str) -> bool:
        """Send a simple email alert"""
        try:
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return False


class SimpleSlackAlert:
    """Standalone Slack alert utility"""
    
    @staticmethod
    def send(webhook_url: str, message: str, channel: Optional[str] = None) -> bool:
        """Send a simple Slack webhook alert"""
        try:
            payload = {'text': message}
            if channel:
                payload['channel'] = channel
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Slack failed: {e}")
            return False