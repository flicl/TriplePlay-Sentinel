# MikroTik Setup Guide

## Overview

Comprehensive guide for configuring MikroTik RouterOS devices for optimal integration with TriplePlay-Sentinel monitoring system. This guide covers API setup, security configuration, and performance optimization.

## Prerequisites

- MikroTik RouterOS 6.45+ (recommended 7.x)
- Administrative access to RouterOS device
- Network connectivity between monitoring system and MikroTik
- Basic understanding of RouterOS configuration

## API Configuration

### Enable API Service

```routeros
# Enable API service
/ip service enable api

# Configure API port (optional, default 8728)
/ip service set api port=8728

# Enable SSL API (recommended for production)
/ip service enable api-ssl
/ip service set api-ssl port=8729
```

### Create Dedicated API User

```routeros
# Create API user group with minimal required permissions
/user group add name=api-readonly policy=api,read,test

# Create API user
/user add name=zabbix-api group=api-readonly password=SecurePassword123!

# Verify user creation
/user print where name=zabbix-api
```

### Advanced User Permissions

For enhanced security, create specific policies:

```routeros
# Create custom policy for monitoring
/user group add name=monitoring policy=api,read,test,sniff

# Add user with custom policy
/user add name=monitoring-user group=monitoring password=MonitoringPass456!

# Set user IP restrictions
/user set monitoring-user allowed-address=192.168.100.0/24
```

## Security Configuration

### API Access Control

```routeros
# Restrict API access by IP
/ip service set api address=192.168.100.10,192.168.100.11

# Configure API-SSL with certificates
/certificate add name=api-cert common-name=router.domain.com
/ip service set api-ssl certificate=api-cert

# Disable unnecessary services
/ip service disable telnet,ftp,www
```

### Firewall Rules

```routeros
# Allow API access from monitoring network
/ip firewall filter add chain=input protocol=tcp dst-port=8728 \
  src-address=192.168.100.0/24 action=accept comment="API Access"

# Allow API-SSL access
/ip firewall filter add chain=input protocol=tcp dst-port=8729 \
  src-address=192.168.100.0/24 action=accept comment="API-SSL Access"

# Block API from other networks
/ip firewall filter add chain=input protocol=tcp dst-port=8728,8729 \
  action=drop comment="Block API from other networks"
```

### Password Policies

```routeros
# Set password requirements
/user settings set minimum-password-length=12
/user settings set minimum-categories=3

# Force password change on first login
/user set [find name=zabbix-api] disabled=no password=TempPassword123!
```

## Performance Optimization

### API Connection Limits

```routeros
# Configure API connection limits
/ip service set api max-sessions=10

# Set connection timeout
/ip service set api timeout=none
```

### Resource Management

```routeros
# Monitor resource usage
/system resource print

# Set CPU usage alerts
/system logging add topics=system action=remote
```

### Interface Configuration

Optimize interfaces for monitoring:

```routeros
# Enable interface statistics
/interface set [find] statistics-enabled=yes

# Configure SNMP for backup monitoring
/snmp set enabled=yes contact="admin@company.com" location="DataCenter-A"
/snmp community set [find] name=public security=none read-access=yes
```

## Monitoring Configuration

### Essential System Items

Configure RouterOS for optimal data collection:

```routeros
# Enable system identity
/system identity set name="Router-DC-01"

# Configure NTP for accurate timestamps
/system ntp client set enabled=yes servers=pool.ntp.org

# Enable logging
/system logging add action=memory topics=system,error,warning
```

### Interface Monitoring

```routeros
# List all interfaces for monitoring setup
/interface print

# Configure interface descriptions
/interface set ether1 comment="WAN-Link-Primary"
/interface set ether2 comment="LAN-Switch-01"

# Enable interface statistics collection
/interface set [find] statistics-enabled=yes
```

### Wireless Configuration (if applicable)

```routeros
# Configure wireless for monitoring
/interface wireless set [find] disabled=no statistics-enabled=yes

# Set wireless security
/interface wireless security-profiles set [find] authentication-types=wpa2-psk

# Configure wireless registration table
/interface wireless registration-table print
```

## Health Monitoring Setup

### CPU and Memory Alerts

```routeros
# Create system health scripts
/system script add name=cpu-alert source={
  :local cpuload [/system resource get cpu-load]
  :if ($cpuload > 80) do={
    :log warning "High CPU usage: $cpuload%"
  }
}

# Schedule health checks
/system scheduler add name=health-check interval=5m \
  on-event=cpu-alert start-time=startup
```

### Temperature Monitoring

```routeros
# Monitor system temperature
/system health print

# Create temperature alert script
/system script add name=temp-alert source={
  :local temp [/system health get [find name=temperature] value]
  :if ($temp > 70) do={
    :log error "High temperature: $temp°C"
  }
}
```

## Backup and Recovery

### Configuration Backup

```routeros
# Create automatic backup
/system backup save name=("backup-" . [/system clock get date])

# Export configuration
/export file=config-backup

# Upload backups to FTP
/tool fetch address=backup-server src-path=backup.backup \
  user=backup-user password=backup-pass upload=yes
```

### Recovery Procedures

```routeros
# Import configuration
/import file-name=config-backup.rsc

# Restore from backup
/system backup load name=backup-file.backup
```

## Integration Testing

### API Connectivity Test

```bash
# Test basic API connection
python3 -c "
import librouteros
api = librouteros.connect('192.168.1.1', username='zabbix-api', password='SecurePassword123!')
print('API Connection: SUCCESS')
result = api('/system/resource/print')
print(f'CPU Load: {result[0]['cpu-load']}%')
api.close()
"
```

### RouterOS Commands for Monitoring

Essential commands for data collection:

```routeros
# System information
/system resource print
/system routerboard print
/system health print

# Interface statistics
/interface print stats
/interface monitor-traffic interface=ether1 duration=5

# Wireless information (if applicable)
/interface wireless print
/interface wireless registration-table print

# System logs
/log print where topics~"system"
```

## Troubleshooting

### Common Issues

1. **API Connection Refused**
   ```routeros
   # Check API service status
   /ip service print where name=api
   
   # Verify firewall rules
   /ip firewall filter print where dst-port=8728
   ```

2. **Authentication Failures**
   ```routeros
   # Check user configuration
   /user print where name=zabbix-api
   
   # Verify group permissions
   /user group print where name=api-readonly
   ```

3. **Permission Denied**
   ```routeros
   # Check user policies
   /user group print detail where name=api-readonly
   
   # Test user permissions
   /user set zabbix-api group=full
   ```

### Diagnostic Commands

```routeros
# Check system status
/system resource print
/system routerboard print

# Monitor connections
/tool netwatch print
/ip firewall connection print

# Check logs
/log print where topics~"system|error"
```

## Security Best Practices

### Regular Maintenance

1. **Update RouterOS regularly**
   ```routeros
   /system package update check-for-updates
   /system package update download
   /system reboot
   ```

2. **Monitor user activity**
   ```routeros
   /user active print
   /log print where topics~"system|login"
   ```

3. **Audit configurations**
   ```routeros
   /user print
   /ip service print
   /ip firewall filter print
   ```

### Certificate Management

```routeros
# Generate self-signed certificate
/certificate add name=api-cert common-name=router.local.domain \
  key-size=2048 days-valid=365 key-usage=digital-signature,key-encipherment

# Sign certificate
/certificate sign api-cert

# Apply to API-SSL
/ip service set api-ssl certificate=api-cert
```

## Performance Baselines

### Expected Response Times

| Operation | Expected Time | Acceptable Limit |
|-----------|---------------|------------------|
| System Resource | < 100ms | 500ms |
| Interface Stats | < 200ms | 1s |
| Wireless Info | < 300ms | 1.5s |
| Route Table | < 500ms | 2s |

### Resource Limits

| Metric | Normal Range | Alert Threshold |
|--------|--------------|-----------------|
| CPU Usage | 0-30% | >80% |
| Memory Usage | 0-60% | >85% |
| Temperature | 30-50°C | >70°C |
| Uptime | Continuous | <24h (after reboot) |

## Integration Checklist

- [ ] API service enabled and configured
- [ ] Dedicated monitoring user created
- [ ] Firewall rules configured
- [ ] SSL certificates installed (production)
- [ ] Interface descriptions set
- [ ] Statistics collection enabled
- [ ] NTP synchronization configured
- [ ] Backup procedures implemented
- [ ] Monitoring integration tested
- [ ] Performance baselines established
