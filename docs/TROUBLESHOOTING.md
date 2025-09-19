# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Receipt Processor system.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues](#common-issues)
- [Error Messages](#error-messages)
- [Performance Issues](#performance-issues)
- [Configuration Issues](#configuration-issues)
- [System Issues](#system-issues)
- [Debug Mode](#debug-mode)
- [Getting Help](#getting-help)

## Quick Diagnostics

### System Health Check

```bash
# Check overall system health
receipt-processor health

# Check specific components
receipt-processor health --show-resources
receipt-processor health --show-alerts
```

### Configuration Validation

```bash
# Validate configuration
receipt-processor config validate

# Show current configuration
receipt-processor config show

# Test all services
receipt-processor test-all
```

### Log Analysis

```bash
# View recent logs
receipt-processor logs --recent 20

# View error logs
receipt-processor error-log --recent 10

# Export logs for analysis
receipt-processor logs --export debug_logs.json
```

## Common Issues

### 1. Installation Issues

#### Problem: "Command not found" after installation

**Symptoms:**
- `receipt-processor: command not found`
- Command not recognized

**Solutions:**

1. **Check PATH environment variable:**
   ```bash
   echo $PATH
   # Should include Python scripts directory
   ```

2. **Reinstall with proper PATH:**
   ```bash
   pip install --user receipt-processor
   # Add ~/.local/bin to PATH
   export PATH="$HOME/.local/bin:$PATH"
   ```

3. **Use Python module directly:**
   ```bash
   python -m receipt_processor --help
   ```

#### Problem: Permission denied errors

**Symptoms:**
- `Permission denied` when running commands
- `Access denied` errors

**Solutions:**

1. **Use virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install receipt-processor
   ```

2. **Install with user flag:**
   ```bash
   pip install --user receipt-processor
   ```

3. **Check file permissions:**
   ```bash
   ls -la /path/to/receipt-processor
   chmod +x /path/to/receipt-processor
   ```

### 2. AI Service Issues

#### Problem: "AI service unavailable" error

**Symptoms:**
- `AI_SERVICE_ERROR` in logs
- `Connection timeout` errors
- `API key invalid` errors

**Solutions:**

1. **Check API key configuration:**
   ```bash
   receipt-processor config show | grep -i api
   ```

2. **Test AI service:**
   ```bash
   receipt-processor test-ai --provider openai
   ```

3. **Verify API key:**
   ```bash
   # Check environment variable
   echo $OPENAI_API_KEY
   
   # Test API key directly
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   ```

4. **Check API quota:**
   - Visit OpenAI dashboard
   - Check usage and billing
   - Verify account status

#### Problem: Low confidence scores

**Symptoms:**
- Confidence scores below threshold
- Inaccurate data extraction
- "No data extracted" errors

**Solutions:**

1. **Improve image quality:**
   - Ensure good lighting
   - Use high resolution images
   - Avoid blurry or distorted images

2. **Adjust confidence threshold:**
   ```bash
   receipt-processor process /path/to/images --confidence 0.7
   ```

3. **Use custom prompts:**
   ```yaml
   ai_vision:
     custom_prompts:
       vendor_extraction: |
         Extract the vendor name from this receipt.
         Look for business names, store names, or company names.
   ```

### 3. Email Issues

#### Problem: Emails not being sent

**Symptoms:**
- `EMAIL_ERROR` in logs
- `SMTP authentication failed`
- `Connection refused` errors

**Solutions:**

1. **Test email configuration:**
   ```bash
   receipt-processor test-email
   ```

2. **Check SMTP settings:**
   ```bash
   receipt-processor config show | grep -i email
   ```

3. **Verify credentials:**
   - Check username and password
   - Use app password for Gmail
   - Enable 2-factor authentication

4. **Test SMTP connection:**
   ```bash
   telnet smtp.gmail.com 587
   ```

#### Problem: Email delivery delays

**Symptoms:**
- Emails sent but not received
- Long delivery times
- Spam folder issues

**Solutions:**

1. **Check spam folder**
2. **Verify sender reputation**
3. **Use proper authentication**
4. **Check email provider limits**

### 4. File Processing Issues

#### Problem: Images not being processed

**Symptoms:**
- Files remain in watch directory
- No processing logs
- "File not found" errors

**Solutions:**

1. **Check file permissions:**
   ```bash
   ls -la /path/to/images
   chmod 644 /path/to/images/*.jpg
   ```

2. **Verify file formats:**
   ```bash
   file /path/to/image.jpg
   # Should show: JPEG image data
   ```

3. **Check file size:**
   ```bash
   ls -lh /path/to/image.jpg
   # Should be reasonable size (not 0 bytes)
   ```

4. **Test with single file:**
   ```bash
   receipt-processor process /path/to/test.jpg --verbose
   ```

#### Problem: Processing errors

**Symptoms:**
- `PROCESSING_ERROR` in logs
- Files stuck in processing state
- Timeout errors

**Solutions:**

1. **Check system resources:**
   ```bash
   receipt-processor health --show-resources
   ```

2. **Reduce batch size:**
   ```bash
   receipt-processor process /path/to/images --batch-size 1
   ```

3. **Increase timeout:**
   ```yaml
   processing:
     timeout: 120
   ```

4. **Check error logs:**
   ```bash
   receipt-processor error-log --recent 10
   ```

### 5. Performance Issues

#### Problem: Slow processing

**Symptoms:**
- Long processing times
- High CPU usage
- Memory issues

**Solutions:**

1. **Check system resources:**
   ```bash
   receipt-processor health --show-resources
   ```

2. **Adjust worker count:**
   ```bash
   receipt-processor daemon-start --max-workers 2
   ```

3. **Optimize batch size:**
   ```bash
   receipt-processor process /path/to/images --batch-size 5
   ```

4. **Check for bottlenecks:**
   ```bash
   receipt-processor metrics --duration 60
   ```

#### Problem: High memory usage

**Symptoms:**
- System running out of memory
- Slow performance
- Out of memory errors

**Solutions:**

1. **Reduce worker count:**
   ```yaml
   processing:
     max_workers: 2
   ```

2. **Set memory limits:**
   ```yaml
   processing:
     resource_limits:
       memory_limit_mb: 512
   ```

3. **Enable garbage collection:**
   ```yaml
   processing:
     enable_gc: true
     gc_interval: 100
   ```

## Error Messages

### AI Service Errors

#### `AI_SERVICE_ERROR: API key invalid`

**Cause:** Invalid or expired API key

**Solution:**
```bash
# Check API key
echo $OPENAI_API_KEY

# Update API key
export OPENAI_API_KEY="your_new_api_key"

# Test API key
receipt-processor test-ai --provider openai
```

#### `AI_SERVICE_ERROR: Rate limit exceeded`

**Cause:** API rate limit exceeded

**Solution:**
```bash
# Wait and retry
sleep 60
receipt-processor process /path/to/images

# Reduce batch size
receipt-processor process /path/to/images --batch-size 1
```

#### `AI_SERVICE_ERROR: Model not available`

**Cause:** Requested model not available

**Solution:**
```yaml
ai_vision:
  model: "gpt-4-vision-preview"  # Use available model
```

### Processing Errors

#### `PROCESSING_ERROR: Image format not supported`

**Cause:** Unsupported image format

**Solution:**
```bash
# Convert image format
convert image.tiff image.jpg

# Check supported formats
receipt-processor config show | grep -i format
```

#### `PROCESSING_ERROR: Confidence threshold not met`

**Cause:** Low confidence score

**Solution:**
```bash
# Lower confidence threshold
receipt-processor process /path/to/images --confidence 0.7

# Improve image quality
# Use better lighting and resolution
```

#### `PROCESSING_ERROR: Timeout exceeded`

**Cause:** Processing timeout

**Solution:**
```yaml
processing:
  timeout: 120  # Increase timeout
```

### Storage Errors

#### `STORAGE_ERROR: Disk space full`

**Cause:** Insufficient disk space

**Solution:**
```bash
# Check disk space
df -h

# Clean up old logs
receipt-processor logs --cleanup --older-than 7

# Move to different directory
receipt-processor config set storage.log_file /path/to/larger/disk/log.json
```

#### `STORAGE_ERROR: Permission denied`

**Cause:** Insufficient file permissions

**Solution:**
```bash
# Check permissions
ls -la /path/to/log/file

# Fix permissions
chmod 644 /path/to/log/file
chown user:group /path/to/log/file
```

### Network Errors

#### `NETWORK_ERROR: Connection timeout`

**Cause:** Network connectivity issues

**Solution:**
```bash
# Test connectivity
ping api.openai.com

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Increase timeout
receipt-processor config set ai_vision.timeout 60
```

#### `NETWORK_ERROR: DNS resolution failed`

**Cause:** DNS issues

**Solution:**
```bash
# Test DNS
nslookup api.openai.com

# Use different DNS
echo "8.8.8.8" > /etc/resolv.conf
```

## Performance Issues

### High CPU Usage

**Symptoms:**
- CPU usage above 80%
- System slowdown
- High temperature

**Solutions:**

1. **Reduce worker count:**
   ```yaml
   processing:
     max_workers: 2
   ```

2. **Enable CPU limiting:**
   ```yaml
   processing:
     resource_limits:
       cpu_limit_percent: 70.0
   ```

3. **Optimize batch processing:**
   ```yaml
   processing:
     batch_size: 5
     parallel_processing: false
   ```

### High Memory Usage

**Symptoms:**
- Memory usage above 80%
- Out of memory errors
- System swapping

**Solutions:**

1. **Set memory limits:**
   ```yaml
   processing:
     resource_limits:
       memory_limit_mb: 1024
   ```

2. **Enable garbage collection:**
   ```yaml
   processing:
     enable_gc: true
     gc_interval: 50
   ```

3. **Reduce batch size:**
   ```yaml
   processing:
     batch_size: 5
   ```

### Slow Processing

**Symptoms:**
- Long processing times
- Low throughput
- Timeout errors

**Solutions:**

1. **Check system resources:**
   ```bash
   receipt-processor health --show-resources
   ```

2. **Optimize configuration:**
   ```yaml
   processing:
     max_workers: 4
     batch_size: 10
     timeout: 120
   ```

3. **Use faster AI model:**
   ```yaml
   ai_vision:
     model: "gpt-4-vision-preview"  # Faster model
   ```

## Configuration Issues

### Invalid Configuration

**Symptoms:**
- `CONFIG_ERROR: Invalid configuration`
- `ValidationError` messages
- Service won't start

**Solutions:**

1. **Validate configuration:**
   ```bash
   receipt-processor config validate
   ```

2. **Check configuration syntax:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

3. **Reset to defaults:**
   ```bash
   receipt-processor config reset
   ```

### Missing Configuration

**Symptoms:**
- `CONFIG_ERROR: Missing required configuration`
- Service fails to start
- Default values used

**Solutions:**

1. **Check required settings:**
   ```bash
   receipt-processor config show
   ```

2. **Set missing values:**
   ```bash
   receipt-processor config set ai_vision.api_key "your_key"
   ```

3. **Use environment variables:**
   ```bash
   export OPENAI_API_KEY="your_key"
   ```

## System Issues

### Service Won't Start

**Symptoms:**
- Daemon fails to start
- Service status shows error
- No logs generated

**Solutions:**

1. **Check system requirements:**
   ```bash
   receipt-processor check-requirements
   ```

2. **Check port availability:**
   ```bash
   netstat -tulpn | grep :8000
   ```

3. **Check file permissions:**
   ```bash
   ls -la /path/to/receipt-processor
   ```

4. **Run in foreground:**
   ```bash
   receipt-processor daemon-start --foreground
   ```

### Service Crashes

**Symptoms:**
- Service stops unexpectedly
- Error logs show crash
- System becomes unresponsive

**Solutions:**

1. **Check crash logs:**
   ```bash
   receipt-processor logs --level error
   ```

2. **Check system resources:**
   ```bash
   receipt-processor health --show-resources
   ```

3. **Enable debug mode:**
   ```bash
   export RECEIPT_PROCESSOR_DEBUG=1
   receipt-processor daemon-start
   ```

4. **Restart service:**
   ```bash
   receipt-processor daemon-stop
   receipt-processor daemon-start
   ```

## Debug Mode

### Enable Debug Mode

```bash
# Set debug environment variable
export RECEIPT_PROCESSOR_DEBUG=1

# Run with debug output
receipt-processor process /path/to/images --verbose --debug
```

### Debug Logging

```yaml
logging:
  level: "DEBUG"
  handlers:
    console:
      enabled: true
      level: "DEBUG"
    file:
      enabled: true
      level: "DEBUG"
      filename: "debug.log"
```

### Debug Commands

```bash
# Show debug information
receipt-processor debug --show-config
receipt-processor debug --show-environment
receipt-processor debug --show-dependencies

# Run diagnostics
receipt-processor diagnose

# Check system requirements
receipt-processor check-requirements
```

## Getting Help

### Self-Help Resources

1. **Check documentation:**
   - [User Manual](USER_MANUAL.md)
   - [API Documentation](API_DOCUMENTATION.md)
   - [Configuration Reference](CONFIGURATION_REFERENCE.md)

2. **Run diagnostics:**
   ```bash
   receipt-processor diagnose
   receipt-processor check-requirements
   receipt-processor test-all
   ```

3. **Check logs:**
   ```bash
   receipt-processor logs --level debug
   receipt-processor error-log --recent 20
   ```

### Community Support

1. **GitHub Issues:**
   - [Report bugs](https://github.com/receipt-processor/receipt-processor/issues)
   - [Request features](https://github.com/receipt-processor/receipt-processor/issues)
   - [Ask questions](https://github.com/receipt-processor/receipt-processor/discussions)

2. **Documentation:**
   - [Online docs](https://receipt-processor.readthedocs.io)
   - [FAQ](https://receipt-processor.readthedocs.io/faq)
   - [Examples](https://receipt-processor.readthedocs.io/examples)

### Professional Support

1. **Email Support:**
   - support@receipt-processor.com
   - Include debug logs and system information

2. **Enterprise Support:**
   - enterprise@receipt-processor.com
   - Priority support for enterprise customers

### Reporting Issues

When reporting issues, include:

1. **System Information:**
   ```bash
   receipt-processor diagnose > system_info.txt
   ```

2. **Configuration:**
   ```bash
   receipt-processor config show > config.txt
   ```

3. **Error Logs:**
   ```bash
   receipt-processor error-log --export error_logs.json
   ```

4. **Steps to Reproduce:**
   - Detailed steps to reproduce the issue
   - Expected vs actual behavior
   - Screenshots if applicable

---

For additional help, please refer to the [User Manual](USER_MANUAL.md) or [API Documentation](API_DOCUMENTATION.md).
