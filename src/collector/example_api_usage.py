#!/usr/bin/env python3
"""
TriplePlay-Sentinel API Client Example
Professional demonstration of the API-Only architecture with librouteros.

This example shows how to interact with the TriplePlay-Sentinel monitoring system
using its REST API for MikroTik device management and monitoring.

Author: TriplePlay-Sentinel Team
License: MIT
"""

import os
import sys
import requests
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List

class TriplePlaySentinelClient:
    """Professional client for TriplePlay-Sentinel API interaction."""
    
    def __init__(self, base_url: str = "http://localhost:5000", api_key: Optional[str] = None):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the TriplePlay-Sentinel API
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api/v2"
        self.api_key = api_key or os.getenv('TRIPLEPLAY_API_KEY')
        self.session = requests.Session()
        
        # Set authentication headers if API key is provided
        if self.api_key:
            self.session.headers.update({
                'X-API-Key': self.api_key,
                'Authorization': f'Bearer {self.api_key}'
            })
        
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TriplePlay-Sentinel-Client/2.0.0'
        })

# Configuration from environment variables or defaults
MIKROTIK_CONFIG = {
    "host": os.getenv('MIKROTIK_HOST', '192.168.1.1'),
    "username": os.getenv('MIKROTIK_USERNAME', 'admin'), 
    "password": os.getenv('MIKROTIK_PASSWORD', 'password')
}

    def test_connection(self, mikrotik_config: Dict[str, str]) -> bool:
        """
        Test connection to MikroTik device via API.
        
        Args:
            mikrotik_config: MikroTik connection configuration
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        print("=== Testing MikroTik API Connection ===")
        
        try:
            response = self.session.post(
                f"{self.api_base}/test-connection",
                json=mikrotik_config,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Connection time: {result.get('connection_time_seconds', 0):.3f}s")
            print(f"Method: {result.get('method', 'API')}")
            
            return result.get('status') == 'success'
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection test failed: {str(e)}")
            return False

    def ping_multiple_targets(self, mikrotik_config: Dict[str, str], 
                             targets: List[str] = None, count: int = 4) -> Optional[Dict[str, Any]]:
        """
        Execute parallel ping to multiple targets.
        
        Args:
            mikrotik_config: MikroTik connection configuration
            targets: List of target IPs/hostnames to ping
            count: Number of ping packets per target
            
        Returns:
            Dict containing ping results or None if failed
        """
        print("\n=== Parallel Ping to Multiple Targets ===")
        
        if targets is None:
            targets = ["8.8.8.8", "1.1.1.1", "208.67.222.222", "9.9.9.9"]
        
        ping_data = {
            **mikrotik_config,
            "targets": targets,
            "count": count,
            "use_cache": True
        }
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.api_base}/mikrotik/ping", 
                json=ping_data,
                timeout=60
            )
            response.raise_for_status()
            execution_time = time.time() - start_time
            
            result = response.json()
            print(f"Method: {result.get('method', 'API')}")
            print(f"Targets: {result.get('targets_requested', 0)}")
            print(f"Successful: {result.get('targets_successful', 0)}")
            print(f"Total time: {execution_time:.3f}s")
            print(f"Avg ping time: {result.get('avg_ping_time_ms', 0):.1f}ms")
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Ping operation failed: {str(e)}")
            return None

    def execute_batch_commands(self, mikrotik_config: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Execute multiple MikroTik commands in batch.
        
        Args:
            mikrotik_config: MikroTik connection configuration
            
        Returns:
            Dict containing batch execution results or None if failed
        """
        print("\n=== Batch Command Execution ===")
        
        batch_data = {
            **mikrotik_config,
            "commands": [
                {
                    "command": "/system/identity/print",
                    "parameters": {},
                    "use_cache": True
                },
                {
                    "command": "/system/resource/print",
                    "parameters": {},
                    "use_cache": True
                },
                {
                    "command": "/interface/print",
                    "parameters": {"stats": "yes"},
                    "use_cache": False
                },
                {
                    "command": "/ip/route/print",
                    "parameters": {"active": "yes"},
                    "use_cache": True
                }
            ],
            "max_concurrent": 4
        }
        
        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.api_base}/mikrotik/batch", 
                json=batch_data,
                timeout=60
            )
            response.raise_for_status()
            execution_time = time.time() - start_time
            
            result = response.json()
            print(f"Method: {result.get('method', 'API')}")
            print(f"Commands: {result.get('commands_requested', 0)}")
            print(f"Successful: {result.get('commands_successful', 0)}")
            print(f"Concurrency: {result.get('max_concurrent', 1)}")
            print(f"Total time: {execution_time:.3f}s")
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Batch execution failed: {str(e)}")
            return None

def multi_host_monitoring():
    """Demonstra monitoramento de múltiplos MikroTiks"""
    print("\n=== Monitoramento Multi-Host ===")
    
    # Configuração para múltiplos MikroTiks
    multi_host_data = {
        "hosts": [
            {
                "host": "192.168.1.1",
                "username": "admin",
                "password": "password",
                "name": "Router-Principal"
            },
            {
                "host": "192.168.2.1", 
                "username": "admin",
                "password": "password",
                "name": "Router-Filial-1"
            },
            {
                "host": "192.168.3.1",
                "username": "admin", 
                "password": "password",
                "name": "Router-Filial-2"
            }
        ],
        "command": "/system/resource/print",
        "parameters": {},
        "max_concurrent_hosts": 3
    }
    
    start_time = time.time()
    response = requests.post(f"{API_BASE}/mikrotik/multi-host", json=multi_host_data)
    execution_time = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        print(f"Método: {result['method']}")
        print(f"Hosts: {result['hosts_requested']}")
        print(f"Sucessos: {result['hosts_successful']}")
        print(f"Concorrência: {result['max_concurrent_hosts']}")
        print(f"Tempo total: {execution_time:.3f}s")
        return result
    else:
        print(f"Erro: {response.status_code}")
        print(response.text)
        return None

    def get_system_stats(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve system statistics and performance metrics.
        
        Returns:
            Dict containing system statistics or None if failed
        """
        print("\n=== System Statistics ===")
        
        try:
            response = self.session.get(f"{self.api_base}/stats", timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            app_stats = result.get('application', {})
            mikrotik_stats = result.get('mikrotik_connector', {})
            config_stats = result.get('configuration', {})
            
            print(f"Version: {app_stats.get('version', 'unknown')}")
            print(f"Mode: {app_stats.get('mode', 'unknown')}")
            print(f"Uptime: {app_stats.get('uptime_seconds', 0):.0f}s")
            print(f"Total requests: {app_stats.get('total_requests', 0)}")
            print(f"Success rate: {app_stats.get('success_rate_percent', 0):.1f}%")
            print(f"Avg response time: {app_stats.get('avg_response_time_seconds', 0):.3f}s")
            print(f"Peak concurrent requests: {app_stats.get('peak_concurrent_requests', 0)}")
            
            print(f"\nActive connections: {mikrotik_stats.get('active_connections', 0)}")
            print(f"Connection pool size: {mikrotik_stats.get('pool_size', 0)}")
            print(f"Cache hits: {mikrotik_stats.get('cache_hits', 0)}")
            print(f"Cache total: {mikrotik_stats.get('cache_total', 0)}")
            
            print(f"\nMax concurrency:")
            print(f"  Hosts: {config_stats.get('max_concurrent_hosts', 0)}")
            print(f"  Commands: {config_stats.get('max_concurrent_commands', 0)}")
            print(f"  Connections per host: {config_stats.get('max_connections_per_host', 0)}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to retrieve statistics: {str(e)}")
            return None

    def clear_cache(self) -> bool:
        """
        Clear system cache.
        
        Returns:
            bool: True if cache cleared successfully, False otherwise
        """
        print("\n=== Clearing System Cache ===")
        
        try:
            response = self.session.post(f"{self.api_base}/cache/clear", timeout=30)
            response.raise_for_status()
            
            result = response.json()
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Message: {result.get('message', 'No message')}")
            
            return result.get('status') == 'success'
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to clear cache: {str(e)}")
            return False

def run_demonstration(client: TriplePlaySentinelClient, mikrotik_config: Dict[str, str]):
    """
    Run a complete demonstration of API capabilities.
    
    Args:
        client: TriplePlaySentinelClient instance
        mikrotik_config: MikroTik connection configuration
    """
    print("TriplePlay-Sentinel API-Only Demonstration")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Base URL: {client.base_url}")
    print(f"Authentication: {'Enabled' if client.api_key else 'Disabled'}")
    
    success_count = 0
    total_tests = 0
    
    try:
        # 1. Test connection
        total_tests += 1
        if client.test_connection(mikrotik_config):
            print("✅ Connection test passed!")
            success_count += 1
        else:
            print("❌ Connection test failed!")
            return
        
        # 2. Test parallel ping
        total_tests += 1
        ping_result = client.ping_multiple_targets(mikrotik_config)
        if ping_result and ping_result.get('status') == 'completed':
            print("✅ Parallel ping test passed!")
            success_count += 1
        else:
            print("❌ Parallel ping test failed!")
        
        # 3. Test batch commands
        total_tests += 1
        batch_result = client.execute_batch_commands(mikrotik_config)
        if batch_result and batch_result.get('status') == 'completed':
            print("✅ Batch command test passed!")
            success_count += 1
        else:
            print("❌ Batch command test failed!")
        
        # 4. Get system statistics
        total_tests += 1
        stats_result = client.get_system_stats()
        if stats_result:
            print("✅ Statistics retrieval passed!")
            success_count += 1
        else:
            print("❌ Statistics retrieval failed!")
        
        # 5. Clear cache
        total_tests += 1
        if client.clear_cache():
            print("✅ Cache clear test passed!")
            success_count += 1
        else:
            print("❌ Cache clear test failed!")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"🎯 Test Summary: {success_count}/{total_tests} tests passed")
        success_rate = (success_count / total_tests) * 100
        
        if success_rate == 100:
            print("🎉 All tests completed successfully!")
        elif success_rate >= 80:
            print("⚠️  Most tests completed successfully!")
        else:
            print("❌ Multiple test failures detected!")
        
        print(f"Success rate: {success_rate:.1f}%")
        
        print("\n💡 TriplePlay-Sentinel API-Only Features:")
        print("   • High-performance MikroTik API integration")
        print("   • Connection pooling and batch processing")
        print("   • Intelligent caching system")
        print("   • Real-time monitoring and statistics")
        print("   • No SSH dependencies - pure API approach")
        
    except KeyboardInterrupt:
        print("\n⚠️ Demonstration interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error during demonstration: {str(e)}")


def main():
    """
    Main entry point with command-line argument support.
    """
    parser = argparse.ArgumentParser(
        description='TriplePlay-Sentinel API Client Demonstration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  TRIPLEPLAY_API_URL      Base URL for the API (default: http://localhost:5000)
  TRIPLEPLAY_API_KEY      API key for authentication
  MIKROTIK_HOST          MikroTik device IP address (default: 192.168.1.1)
  MIKROTIK_USERNAME      MikroTik username (default: admin)
  MIKROTIK_PASSWORD      MikroTik password (default: password)

Examples:
  python example_api_usage.py
  python example_api_usage.py --url http://my-server:5000
  python example_api_usage.py --mikrotik-host 10.0.0.1 --mikrotik-user monitor
        """
    )
    
    parser.add_argument(
        '--url', 
        default=os.getenv('TRIPLEPLAY_API_URL', 'http://localhost:5000'),
        help='Base URL for TriplePlay-Sentinel API'
    )
    parser.add_argument(
        '--api-key',
        default=os.getenv('TRIPLEPLAY_API_KEY'),
        help='API key for authentication'
    )
    parser.add_argument(
        '--mikrotik-host',
        default=os.getenv('MIKROTIK_HOST', '192.168.1.1'),
        help='MikroTik device IP address'
    )
    parser.add_argument(
        '--mikrotik-user',
        default=os.getenv('MIKROTIK_USERNAME', 'admin'),
        help='MikroTik username'
    )
    parser.add_argument(
        '--mikrotik-password',
        default=os.getenv('MIKROTIK_PASSWORD', 'password'),
        help='MikroTik password'
    )
    parser.add_argument(
        '--ping-targets',
        nargs='+',
        default=['8.8.8.8', '1.1.1.1'],
        help='Target IPs for ping test'
    )
    parser.add_argument(
        '--ping-count',
        type=int,
        default=4,
        help='Number of ping packets per target'
    )
    
    args = parser.parse_args()
    
    # Create client
    client = TriplePlaySentinelClient(
        base_url=args.url,
        api_key=args.api_key
    )
    
    # Configure MikroTik connection
    mikrotik_config = {
        "host": args.mikrotik_host,
        "username": args.mikrotik_user,
        "password": args.mikrotik_password
    }
    
    # Validate configuration
    if not all([args.mikrotik_host, args.mikrotik_user, args.mikrotik_password]):
        print("❌ Error: MikroTik connection parameters are incomplete!")
        print("Please provide --mikrotik-host, --mikrotik-user, and --mikrotik-password")
        sys.exit(1)
    
    try:
        # Run demonstration
        run_demonstration(client, mikrotik_config)
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Unable to connect to TriplePlay-Sentinel at {args.url}")
        print("   Please ensure the service is running and accessible")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
