"""
Unit tests for disk monitor
"""

import unittest
from lib.disk_checker import DiskChecker, DiskUsage


class TestDiskChecker(unittest.TestCase):
    """Test cases for DiskChecker class"""
    
    def test_parse_df_output(self):
        """Test parsing df command output"""
        df_output = """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   40G   10G  80% /
/dev/sdb1       100G   85G   15G  85% /data
tmpfs           7.8G  1.2G  6.6G  16% /tmp"""
        
        disk_usages = DiskChecker.parse_df_output(df_output)
        
        self.assertEqual(len(disk_usages), 3)
        self.assertEqual(disk_usages[0].filesystem, '/dev/sda1')
        self.assertEqual(disk_usages[0].use_percent, 80)
        self.assertEqual(disk_usages[0].mounted_on, '/')
        
    def test_check_threshold(self):
        """Test threshold checking"""
        disk_usages = [
            DiskUsage('/dev/sda1', '50G', '40G', '10G', 80, '/'),
            DiskUsage('/dev/sdb1', '100G', '50G', '50G', 50, '/data'),
            DiskUsage('/dev/sdc1', '100G', '95G', '5G', 95, '/backup')
        ]
        
        exceeding = DiskChecker.check_threshold(disk_usages, 80)
        
        self.assertEqual(len(exceeding), 2)
        self.assertEqual(exceeding[0].use_percent, 80)
        self.assertEqual(exceeding[1].use_percent, 95)
    
    def test_format_alert_message(self):
        """Test alert message formatting"""
        disk_usages = [
            DiskUsage('/dev/sda1', '50G', '45G', '5G', 90, '/')
        ]
        
        message = DiskChecker.format_alert_message('192.168.1.10', disk_usages, 80)
        
        self.assertIn('192.168.1.10', message)
        self.assertIn('90%', message)
        self.assertIn('/', message)


if __name__ == '__main__':
    unittest.main()