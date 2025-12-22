# Development Scripts

## test_device.py

Test script for the BlueBOLT device communication layer.

**Usage:**

```bash
# Using environment variables
BLUEBOLT_HOST=192.168.0.162 BLUEBOLT_MAC=1065a3XXXXXX python scripts/test_device.py

# Using command line arguments
python scripts/test_device.py 192.168.0.162 1065a3XXXXXX
```

**Security Note:**

The last 6 characters of the MAC address are sensitive because the card uses them for authentication.
