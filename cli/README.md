# lsec CLI

A command-line interface for managing and linking environment variables across multiple projects.

## Features

- **Export Variables**: Export project variables to `.env` files with prefix/suffix support
- **Import Variables**: Import variables from `.env` files with smart conflict resolution
- **Check Updates**: Detect outdated exports and suggest re-export commands
- **Diff Viewing**: Compare stored exports with current variable values
- **Project Management**: List projects and their variables
- **Rich Output**: Beautiful terminal output with tables and colors

## Installation

### System-wide Installation (Recommended)

```bash
# From the project root directory
cd cli
pip install -e .

# Now you can use the lsec command from anywhere
lsec --help
```

### Development Setup

```bash
cd cli
pip install -r requirements.txt
python -m secretool.main --help
```

## Usage

### Basic Commands

```bash
# Show help
lsec --help

# Show status and configuration
lsec status

# List all projects
lsec projects

# List variables for a project
lsec variables --project webapp
```

### Export Variables

```bash
# Export project variables to .env file
lsec export --project webapp --out-dir ./config

# Export with prefix
lsec export --project webapp --prefix WEBAPP_

# Export with suffix
lsec export --project webapp --suffix _PROD

# Dry run to see what would be exported
lsec export --project webapp --dry-run

# Verbose output
lsec export --project webapp --verbose
```

### Import Variables

```bash
# Import from .env file
lsec import-env --project webapp --env-file .env

# Preview before importing
lsec import-env --project webapp --env-file .env --preview

# Import with transformations
lsec import-env --project webapp --env-file .env \
  --strip-prefix "PROD_" --add-prefix "DEV_"

# Import with custom description
lsec import-env --project webapp --env-file .env \
  --description "Development configuration"
```

### Check for Updates

```bash
# Check all exports for updates
lsec check-updates

# Check specific project
lsec check-updates --project webapp

# Verbose output
lsec check-updates --verbose
```

### View Differences

```bash
# Show diff for specific export
lsec diff --export-id 1

# Show unchanged variables too
lsec diff --export-id 1 --show-unchanged

# Verbose output
lsec diff --export-id 1 --verbose
```

## Configuration

### Environment Variables

- `LSEC_API_URL`: API base URL (default: http://localhost:8088)
- `LSEC_API_TIMEOUT`: API timeout in seconds (default: 30)
- `LSEC_DEFAULT_PROJECT`: Default project name
- `LSEC_OUTPUT_DIR`: Default output directory (default: .)
- `LSEC_ENV_FILE`: Environment file name (default: .env)
- `LSEC_VERBOSE`: Enable verbose output (default: false)
- `LSEC_QUIET`: Enable quiet output (default: false)

### Example Configuration

```bash
export LSEC_API_URL="http://localhost:8088"
export LSEC_DEFAULT_PROJECT="webapp"
export LSEC_OUTPUT_DIR="./config"
export LSEC_VERBOSE="true"
```

## Examples

### Export Workflow

```bash
# 1. Check what projects are available
lsec projects

# 2. See variables in a project
lsec variables --project webapp

# 3. Export variables
lsec export --project webapp --out-dir ./config

# 4. Check for updates later
lsec check-updates

# 5. View differences if updates are found
lsec diff --export-id 1
```

### Development Workflow

```bash
# Set default project for convenience
export LSEC_DEFAULT_PROJECT="webapp"

# Export with development prefix
lsec export --prefix DEV_ --out-dir ./dev-config

# Check for updates
lsec check-updates

# Re-export if needed
lsec export --prefix DEV_ --out-dir ./dev-config
```

## Error Handling

The CLI provides clear error messages and suggestions:

- **Project not found**: Shows available projects
- **API connection issues**: Provides troubleshooting steps
- **Export failures**: Shows partial success and suggests fixes
- **Validation errors**: Explains what went wrong

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Ensure the backend API is running
   - Check `LSEC_API_URL` environment variable
   - Verify network connectivity

2. **Project Not Found**
   - Use `lsec projects` to see available projects
   - Check project name spelling
   - Set `LSEC_DEFAULT_PROJECT` for convenience

3. **Export Permission Denied**
   - Check write permissions for output directory
   - Ensure directory exists or can be created

### Debug Mode

Use `--verbose` flag for detailed output:

```bash
lsec export --project webapp --verbose
```

This will show:
- API health checks
- Project lookups
- Variable resolution steps
- File operations
- Error details 