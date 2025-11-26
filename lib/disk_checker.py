"""
Disk Checker Module
Disk usage monitoring and analysis
"""

import re
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DiskUsage:
    """Represents disk usage information for a filesystem"""
    filesystem: str
    size: str
    used: str
    available: str
    use_percent: int
    mounted_on: str


class DiskChecker:
    """Checks disk usage on remote systems"""
    
    @staticmethod
    def parse_df_output(df_output: str) -> List[DiskUsage]:
        """
        Parse 'df -h' command output
        
        Args:
            df_output: Output from df command
            
        Returns:
            List of DiskUsage objects
        """
        disk_usages = []
        lines = df_output.strip().split('\n')
        
        # Skip header line
        for line in lines[1:]:
            parts = line.split()
            
            # Handle wrapped lines or unusual formatting
            if len(parts) < 6:
                continue
            
            try:
                # Extract percentage and remove '%' sign
                use_percent_str = parts[4].rstrip('%')
                use_percent = int(use_percent_str)
                
                disk_usage = DiskUsage(
                    filesystem=parts[0],
                    size=parts[1],
                    used=parts[2],
                    available=parts[3],
                    use_percent=use_percent,
                    mounted_on=parts[5] if len(parts) > 5 else parts[5]
                )
                
                disk_usages.append(disk_usage)
                logger.debug(f"Parsed: {disk_usage.mounted_on} -> {disk_usage.use_percent}%")
                
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse line: {line} - {e}")
                continue
        
        return disk_usages
    
    @staticmethod
    def check_threshold(disk_usages: List[DiskUsage], threshold: int) -> List[DiskUsage]:
        """
        Filter disk usages that exceed threshold
        
        Args:
            disk_usages: List of DiskUsage objects
            threshold: Percentage threshold
            
        Returns:
            List of DiskUsage objects exceeding threshold
        """
        exceeding = [du for du in disk_usages if du.use_percent >= threshold]
        
        if exceeding:
            logger.warning(f"Found {len(exceeding)} filesystems exceeding {threshold}%")
        else:
            logger.info(f"All filesystems below {threshold}% threshold")
        
        return exceeding
    
    @staticmethod
    def format_alert_message(host: str, disk_usages: List[DiskUsage], threshold: int) -> str:
        """
        Format disk usage alert message
        
        Args:
            host: Server hostname/IP
            disk_usages: List of DiskUsage objects exceeding threshold
            threshold: Threshold percentage
            
        Returns:
            Formatted alert message
        """
        message_lines = [
            f"⚠️  Disk Usage Alert for {host}",
            f"Threshold: {threshold}%",
            "",
            "Filesystems exceeding threshold:",
            ""
        ]
        
        for du in disk_usages:
            message_lines.append(
                f"  • {du.mounted_on}: {du.use_percent}% "
                f"({du.used}/{du.size}) - {du.filesystem}"
            )
        
        return "\n".join(message_lines)