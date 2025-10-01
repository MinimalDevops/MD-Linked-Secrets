# MD-Linked-Secrets 🔐

**A powerful environment variable management system for multi-project development**

![Dashboard](images/dashboard.png)
*Main dashboard showing project overview and quick access to all features*

## 🚀 Why MD-Linked-Secrets?

### The Problem
When working on multiple projects (especially open-source and local projects), you often face these challenges:

- **API Endpoint Chaos**: APIs and endpoints change over time, and you forget where you used them across different projects
- **Environment Variable Complexity**: Storing environment variables permanently in your system is complicated and messy
- **Cross-Project Dependencies**: Variables from one project need to be used in another, but there's no centralized way to manage them
- **Export Tracking**: You export variables to different locations but lose track of where and when
- **Version Control Issues**: Hardcoding sensitive values in your code or losing track of configuration changes

### The Solution
MD-Linked-Secrets provides a centralized, intelligent environment variable management system that:

- **Centralizes Configuration**: Store all your environment variables in one place
- **Cross-Project Linking**: Link variables between projects using `PROJECT:VARIABLE` syntax
- **Smart Concatenation**: Combine multiple variables with custom separators
- **Export Tracking**: Track where you've exported variables with git repository information
- **Impact Analysis**: See exactly which projects and exports will be affected by variable changes
- **Version Control**: Keep your sensitive data out of git while maintaining configuration history

## ✨ Key Features

### 🔗 **Variable Linking**
```bash
# Link variables across projects
API_URL=Project1:API_BASE_URL
DATABASE_URL=Project1:DB_HOST:Project1:DB_PORT
```

![Linked Variables](images/vars_in_project_linked_concatenated.png)
*Variables linked and concatenated across different projects*

### 🔄 **Smart Concatenation**
```bash
# Combine multiple variables with custom separators
FULL_URL=Project1:API_BASE_URL|Project1:API_VERSION|Project1:ENDPOINT
```

### 📊 **Impact Analysis**
- See which projects will be affected before making changes
- Track all exports that contain your variables
- View git repository information (branch, commit, remote) for each export

![Impact Analysis](images/impact_analysis%20_audit_tracing.png)
*Comprehensive impact analysis showing which projects and exports will be affected by changes*

### 🎯 **Export Management**
- Export variables to any directory
- Track git repository context (branch, commit hash, remote URL)
- List, filter, and remove tracked exports
- Detect when exported files need updates

![Export History](images/export_history.png)
*Export history tracking with git repository information and export status*

### 🔒 **Security & Privacy**
- **Show/Hide Values**: Toggle between showing and hiding sensitive values in the UI
- **Encrypt sensitive variables**: Protect your secrets with encryption
- **Keep secrets out of version control**: Centralized secret management
- **Audit trail for all changes**: Complete history of who changed what and when

### 📁 **Import & Export Management**
- **Drag & Drop Import**: Import variables by dropping .env files directly into the web interface
- **CLI Import**: Import from files or paste content directly via command line
- **Bulk Operations**: Import multiple variables at once with custom prefixes
- **Export Tracking**: Track all exports with git repository context (branch, commit, remote)

![Import Variables](images/import_environment_vars_page.png)
*Import interface with drag & drop functionality and conflict resolution*

### 🔍 **Search & Discovery**
- **Global Search**: Search across all projects, variables, and values from a single search bar
- **Smart Filtering**: Find variables by name, value, project, or type
- **Quick Navigation**: Jump directly to any variable or project from search results

![Global Search](images/search.png)
*Global search functionality across all projects and variables*

### 📊 **History & Version Control**
- **Variable History**: Track all changes to variables with timestamps and user information
- **Configurable History**: Control how much history to keep per project
- **Rollback Capability**: Revert variables to previous values
- **Change Tracking**: See exactly what changed between versions

![Variable History](images/var_history.png)
*Detailed variable history showing all changes, timestamps, and rollback options*

![Variable Versioning](images/vars_versioning_page.png)
*Variable history and versioning with rollback capabilities*

## 📁 Project Structure

```
MD-Linked-Secrets/
├── backend/                 # FastAPI backend application
│   ├── app/                # Main application code
│   ├── tests/              # Backend tests
│   └── main.py             # Application entry point
├── frontend/               # React frontend application
│   ├── src/                # Source code
│   ├── public/             # Static assets
│   └── package.json        # Dependencies
├── cli/                    # Command-line interface
│   ├── secretool/          # CLI package
│   └── setup.py            # Installation script
├── database/               # Database migration files
│   └── add_git_tracking_fields.sql
├── scripts/                # Utility scripts
│   ├── setup_database.py
│   ├── validate-setup.sh
│   └── test_prefix_suffix_fix.sh
├── example.env             # Environment configuration template
├── ecosystem.config.js     # PM2 configuration
└── README.md               # This file
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Node.js 16+ (for frontend)
- Git

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd MD-Linked-Secrets
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

#### Database Setup
The application uses **SQLAlchemy ORM** to automatically create database tables from Python models. No manual SQL schema files are required.

**Step 1: Configure Environment**
```bash
# Copy the example environment file
cp example.env backend/.env

# Edit the database configuration
# Update DATABASE_URL in backend/.env with your PostgreSQL credentials:
# DATABASE_URL=postgresql://username:password@localhost:5432/md_linked_secrets
```

**Step 2: Create Database**
```bash
# Create PostgreSQL database
createdb md_linked_secrets
```

**Step 3: Setup Tables (Choose one option)**

**Option 1: Automatic Setup (Recommended)**
```bash
# Use the setup script (handles everything automatically)
python scripts/setup_database.py
```

**Option 2: Manual Setup**
```bash
# Start the backend (tables are created automatically on first run)
cd backend
python -c "
from app.core.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('Database tables created successfully!')
"
```

**Option 3: Let the Application Handle It**
```bash
# Start the application - tables are created automatically
pm2 start ecosystem.config.js
# or
python -m uvicorn backend.main:app --reload --port 8088
```

#### Database Schema
The system automatically creates the following tables using SQLAlchemy ORM:

- **`projects`**: Store project information
- **`env_vars`**: Environment variables with linking and concatenation support
- **`project_links`**: Many-to-many relationships between projects
- **`env_exports`**: Track exported variables with git information
- **`env_imports`**: Track imported variables
- **`variable_history`**: Audit trail for variable changes
- **`audit_log`**: General audit logging

#### Git Tracking Enhancement
For enhanced git integration features, run the migration script:
```bash
# Apply git tracking enhancements (optional but recommended)
psql -d md_linked_secrets -f database/add_git_tracking_fields.sql
```

This adds git tracking fields to the `env_exports` table:
- `git_repo_path` - Repository root path
- `git_branch` - Branch name at export time
- `git_commit_hash` - Commit hash
- `git_remote_url` - Remote repository URL
- `is_git_repo` - Whether export was in git repository

#### Start Backend Server
```bash
# Using PM2 (recommended)
pm2 start backend/main.py --name md-secrets-backend --interpreter python

# Or directly
cd backend
python -m uvicorn main:app --reload --port 8088
```

### 3. Frontend Setup

#### Install Dependencies
```bash
cd frontend
npm install
```

#### Start Frontend Server
```bash
# Using PM2 (recommended)
pm2 start "npm start" --name md-secrets-frontend

# Or directly
npm start
```

### 4. CLI Setup

#### Install CLI Tool
```bash
# Navigate to CLI directory
cd cli

# Install in development mode (recommended for local development)
pip install -e .

# Or install globally
pip install .
```

#### Verify Installation
```bash
# Check if CLI is installed correctly
lsec --help

# You should see the MD-Linked-Secrets CLI help menu
```

#### CLI Configuration
The CLI automatically connects to your local backend server. Make sure your backend is running on `http://localhost:8088` before using CLI commands.

> **💡 Tip**: The CLI is the most powerful way to interact with MD-Linked-Secrets. It provides all the functionality of the web interface plus advanced features like batch operations, scripting, and automation. See the [CLI Reference](#-cli-reference) section below for comprehensive usage examples.

## 🎯 Quick Start

### 1. Create Your First Project
```bash
# Using CLI
lsec create-project "My API Project" "Backend API for my application"

# Or using the web interface
# Navigate to http://localhost:3000
```

### 2. Add Environment Variables
```bash
# Add variables to your project
lsec add-var --project "My API Project" --name "API_BASE_URL" --value "https://api.example.com"
lsec add-var --project "My API Project" --name "API_VERSION" --value "v1"
lsec add-var --project "My API Project" --name "DATABASE_URL" --value "postgresql://user:pass@localhost/db"
```

### 3. Create Linked Variables
```bash
# Create a project that uses variables from another project
lsec create-project "My Frontend" "Frontend application"
lsec add-var --project "My Frontend" --name "API_URL" --linked "My API Project:API_BASE_URL"
lsec add-var --project "My Frontend" --name "FULL_API_URL" --concat "My API Project:API_BASE_URL|My API Project:API_VERSION"
```

### 4. Export Variables
```bash
# Export to a specific directory
lsec export --project "My API Project" --out-dir ./my-project/.env

# Export with prefix/suffix
lsec export --project "My API Project" --out-dir ./my-project/.env --prefix "MYAPP_" --suffix "_PROD"
```

### 5. Track and Manage Exports
```bash
# List all exports
lsec list-exports

# Get export summary
lsec export-summary

# Remove an export from tracking
lsec remove-export --export-id 123
```

## 🖥️ CLI Reference

The MD-Linked-Secrets CLI (`lsec`) provides a powerful command-line interface for managing your environment variables. Here's a comprehensive guide:

![CLI Interface](images/cli.png)
*Command-line interface for managing environment variables and projects*

### 📋 **Project Management**

#### Create a New Project
```bash
# Create a project with name and description
lsec create-project "My Project" "Description of my project"

# Create a project with just a name
lsec create-project "My Project"
```

#### List All Projects
```bash
# List all projects with details
lsec list-projects

# List projects with specific format
lsec list-projects --format table
```

#### Get Project Details
```bash
# Get detailed information about a project
lsec get-project "My Project"
```

### 🔧 **Variable Management**

![Add Variable](images/add_variable.png)
*Add new variables with different types: raw values, linked variables, or concatenated values*

#### Add Variables
```bash
# Add a raw variable
lsec add-var --project "My Project" --name "API_URL" --value "https://api.example.com"

# Add a linked variable (references another project's variable)
lsec add-var --project "My Project" --name "EXTERNAL_API" --linked "Other Project:API_URL"

# Add a concatenated variable
lsec add-var --project "My Project" --name "FULL_URL" --concat "My Project:API_URL|My Project:VERSION"

# Add an encrypted variable
lsec add-var --project "My Project" --name "SECRET_KEY" --value "my-secret" --encrypt

# Add variable with description
lsec add-var --project "My Project" --name "DB_HOST" --value "localhost" --description "Database host"
```

#### List Variables
```bash
# List all variables in a project
lsec list-vars --project "My Project"

# List variables with specific format
lsec list-vars --project "My Project" --format json
```

#### Update Variables
```bash
# Update a variable's value
lsec update-var --project "My Project" --name "API_URL" --value "https://new-api.example.com"

# Update variable description
lsec update-var --project "My Project" --name "API_URL" --description "Updated API endpoint"
```

#### Delete Variables
```bash
# Delete a variable
lsec delete-var --project "My Project" --name "OLD_VARIABLE"
```

### 📤 **Export Management**

#### Export Variables
```bash
# Basic export
lsec export --project "My Project" --out-dir ./my-project

# Export with prefix
lsec export --project "My Project" --out-dir ./my-project --prefix "PROD_"

# Export with suffix
lsec export --project "My Project" --out-dir ./my-project --suffix "_V2"

# Export with both prefix and suffix
lsec export --project "My Project" --out-dir ./my-project --prefix "PROD_" --suffix "_V2"

# Dry run (see what would be exported without writing files)
lsec export --project "My Project" --out-dir ./my-project --dry-run

# Verbose output
lsec export --project "My Project" --out-dir ./my-project --verbose
```

#### List Exports
```bash
# List all exports
lsec list-exports

# List exports for a specific project
lsec list-exports --project "My Project"

# List exports by git branch
lsec list-exports --git-branch main

# List only exports in git repositories
lsec list-exports --is-git-repo true

# Limit number of results
lsec list-exports --limit 10
```

#### Export Summary
```bash
# Get summary of all exports
lsec export-summary

# Get summary for specific project
lsec export-summary --project "My Project"
```

#### Remove Exports
```bash
# Remove an export from tracking
lsec remove-export --export-id 123

# Remove multiple exports
lsec remove-export --export-id 123 --export-id 124
```

### 📥 **Import Management**

#### Import Variables
```bash
# Import from a .env file
lsec import --project "My Project" --file ./existing.env

# Import with custom prefix
lsec import --project "My Project" --file ./existing.env --prefix "IMPORTED_"

# Import from clipboard content (paste .env content directly)
lsec import --project "My Project" --content "API_URL=https://api.example.com
DATABASE_URL=postgresql://user:pass@localhost/db"

# Import with overwrite existing variables
lsec import --project "My Project" --file ./existing.env --overwrite

# Import with dry-run (preview what would be imported)
lsec import --project "My Project" --file ./existing.env --dry-run
```

![Conflict Resolution](images/import_vars_conflict_resolution_page.png)
*Conflict resolution interface when importing variables that already exist*

#### List Imports
```bash
# List all imports
lsec list-imports

# List imports for specific project
lsec list-imports --project "My Project"

# List imports with details
lsec list-imports --verbose
```

### 🔍 **Advanced Features**

#### Variable Resolution
```bash
# Resolve a variable (see its final value)
lsec resolve --project "My Project" --name "API_URL"

# Resolve all variables in a project
lsec resolve --project "My Project" --all
```

#### Impact Analysis
```bash
# Get impact analysis for a variable
lsec impact-analysis --project "My Project" --name "API_URL"
```

#### Health Check
```bash
# Check if the backend is running
lsec health-check
```

### 🎨 **Output Formats**

Most CLI commands support different output formats:

```bash
# Table format (default)
lsec list-projects --format table

# JSON format
lsec list-projects --format json

# CSV format
lsec list-projects --format csv
```

### 🔧 **CLI Configuration**

#### Environment Variables
You can configure the CLI using environment variables:

```bash
# Set custom backend URL
export MD_SECRETS_API_URL=http://localhost:8088

# Set custom timeout
export MD_SECRETS_TIMEOUT=30
```

#### Configuration File
Create a `.md-secrets-config.json` file in your home directory:

```json
{
  "api_url": "http://localhost:8088",
  "timeout": 30,
  "default_format": "table",
  "verbose": false
}
```

### 🚀 **Common Workflows**

#### Setting Up a New Project
```bash
# 1. Create project
lsec create-project "My New API" "Backend API for my application"

# 2. Add basic variables
lsec add-var --project "My New API" --name "API_BASE_URL" --value "https://api.example.com"
lsec add-var --project "My New API" --name "API_VERSION" --value "v1"
lsec add-var --project "My New API" --name "DATABASE_URL" --value "postgresql://user:pass@localhost/db"

# 3. Export to your project directory
lsec export --project "My New API" --out-dir ./my-new-api
```

#### Managing Cross-Project Dependencies
```bash
# 1. Create frontend project
lsec create-project "My Frontend" "Frontend application"

# 2. Link to backend variables
lsec add-var --project "My Frontend" --name "API_URL" --linked "My New API:API_BASE_URL"
lsec add-var --project "My Frontend" --name "FULL_API_URL" --concat "My New API:API_BASE_URL|My New API:API_VERSION"

# 3. Export frontend variables
lsec export --project "My Frontend" --out-dir ./my-frontend
```

#### Updating and Tracking Changes
```bash
# 1. Update a variable
lsec update-var --project "My New API" --name "API_BASE_URL" --value "https://new-api.example.com"

# 2. Check impact
lsec impact-analysis --project "My New API" --name "API_BASE_URL"

# 3. Re-export affected projects
lsec export --project "My New API" --out-dir ./my-new-api
lsec export --project "My Frontend" --out-dir ./my-frontend
```

### ❓ **Getting Help**

```bash
# General help
lsec --help

# Help for specific command
lsec export --help
lsec add-var --help

# List all available commands
lsec --help
```

## 🌐 Web Interface

Access the web interface at `http://localhost:3000` to:

![Projects Management](images/projects.png)
*Projects management interface showing all your projects and their details*

### 🎯 **Core Features**
- **Manage Projects**: Create, edit, and organize your projects
- **Variable Management**: Add, edit, and link environment variables
- **Impact Analysis**: See the impact of changes before making them
- **Export Tracking**: View and manage all your exports with git information
- **Visual Linking**: See the relationships between your variables

### 🔍 **Search & Discovery**
- **Global Search Bar**: Search across all projects, variables, and values
- **Smart Filtering**: Filter by project, variable type, or value content
- **Quick Navigation**: Click search results to jump directly to variables
- **Real-time Search**: Instant results as you type

### 📁 **Import & Export**
- **Drag & Drop Import**: Simply drag .env files into the web interface to import
- **Paste Import**: Copy and paste .env content directly into the import dialog
- **Bulk Import**: Import multiple variables at once with custom prefixes
- **Export Management**: View all exports with git repository information
- **Export Actions**: Re-export, untrack, or delete exports directly from the UI

### 🔒 **Security Features**
- **Show/Hide Values**: Toggle between showing and hiding sensitive values
- **Encrypted Variables**: Visual indicators for encrypted variables
- **Secure Display**: Sensitive values are masked by default
- **Access Control**: Control who can see what values

### 📊 **History & Tracking**
- **Variable History**: View complete change history for any variable
- **Configurable History**: Set how much history to keep per project
- **Change Tracking**: See exactly what changed and when
- **Rollback Options**: Revert variables to previous values
- **Audit Trail**: Complete log of all system activities

### 🎨 **User Experience**
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark/Light Theme**: Choose your preferred interface theme
- **Keyboard Shortcuts**: Quick actions for power users
- **Real-time Updates**: Changes are reflected immediately across all connected clients

## 📚 Advanced Usage

### Variable Linking Syntax
```bash
# Simple link
VARIABLE_NAME=ProjectName:VariableName

# Concatenation with separator
FULL_URL=Project1:API_BASE|Project1:API_VERSION|Project1:ENDPOINT

# Mixed linking and concatenation
COMPLEX_URL=Project1:API_BASE|Project2:VERSION|Project1:ENDPOINT
```

### Export Management
```bash
# Export with custom prefix/suffix
lsec export --project "My Project" --out-dir ./output --prefix "PROD_" --suffix "_V2"

# List exports by git branch
lsec list-exports --git-branch main

# List exports in git repositories only
lsec list-exports --is-git-repo true
```

### Impact Analysis
Before making changes to variables, use impact analysis to see:
- Which projects will be affected
- Which exports will need updates
- Git repository information for each export
- Recommendations for safe changes

### History Management
```bash
# Configure history settings for a project
lsec update-project "My Project" --history-enabled true --history-limit 50

# View variable history
lsec variable-history --project "My Project" --name "API_URL"

# Rollback to previous value
lsec rollback-variable --project "My Project" --name "API_URL" --to-version 2

# Clear history for a project
lsec clear-history --project "My Project"
```

### Search & Discovery
```bash
# Search across all projects and variables
lsec search "API_URL"

# Search with filters
lsec search "database" --project "My Project" --type "raw"

# Search in values (not just names)
lsec search "localhost" --search-values true
```

## 🔧 Configuration

### Environment Variables
**⚠️ IMPORTANT:** You must configure the environment file before setting up the database.

Create a `.env` file in the backend directory:

```bash
# Copy the example environment file
cp example.env backend/.env
```

**Required Configuration:**
```bash
# Edit backend/.env and update these values:

# Database (REQUIRED - must match your PostgreSQL setup)
DATABASE_URL=postgresql://username:password@localhost:5432/md_linked_secrets

# Security (REQUIRED - generate your own secure keys)
SECRET_KEY=your-super-secret-key-here-change-this-in-production
ENCRYPTION_KEY=your-encryption-key-here-32-characters-long

# API (Optional - defaults shown)
API_HOST=0.0.0.0
API_PORT=8088
```

**Example DATABASE_URL formats:**
```bash
# Local PostgreSQL with password
DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/md_linked_secrets

# Local PostgreSQL without password (trust authentication)
DATABASE_URL=postgresql://myuser@localhost:5432/md_linked_secrets

# Remote PostgreSQL
DATABASE_URL=postgresql://myuser:mypassword@db.example.com:5432/md_linked_secrets
```

### PM2 Configuration
Create `ecosystem.config.js`:

```javascript
module.exports = {
  apps: [
    {
      name: 'md-secrets-backend',
      script: 'backend/main.py',
      interpreter: 'python',
      args: '-m uvicorn main:app --host 0.0.0.0 --port 8088',
      cwd: './',
      env: {
        NODE_ENV: 'production'
      }
    },
    {
      name: 'md-secrets-frontend',
      script: 'npm',
      args: 'start',
      cwd: './frontend',
      env: {
        NODE_ENV: 'production',
        REACT_APP_API_URL: 'http://localhost:8088'
      }
    }
  ]
};
```

## 🚀 Production Deployment

### Using PM2 (Recommended)

PM2 is the recommended way to run MD-Linked-Secrets in production. It provides process management, automatic restarts, and monitoring.

#### Basic PM2 Commands
```bash
# Start all services using ecosystem file
pm2 start ecosystem.config.js

# Start individual services
pm2 start backend/main.py --name md-secrets-backend --interpreter python
pm2 start "npm start" --name md-secrets-frontend --cwd ./frontend

# Monitor services in real-time
pm2 monit

# View logs
pm2 logs                    # All services
pm2 logs md-secrets-backend # Specific service
pm2 logs --lines 100        # Last 100 lines

# Restart services
pm2 restart all             # All services
pm2 restart md-secrets-backend # Specific service

# Stop services
pm2 stop all
pm2 stop md-secrets-backend

# Delete services
pm2 delete all
pm2 delete md-secrets-backend
```

#### PM2 Process Management
```bash
# List all processes
pm2 list

# Show process details
pm2 show md-secrets-backend

# Reload services (zero-downtime restart)
pm2 reload all

# Save current process list
pm2 save

# Restore saved processes on reboot
pm2 startup
```

#### PM2 Monitoring & Logs
```bash
# Real-time monitoring dashboard
pm2 monit

# View logs with timestamps
pm2 logs --timestamp

# Clear logs
pm2 flush

# Set log rotation
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 30
```

#### PM2 Environment Management
```bash
# Start with specific environment
pm2 start ecosystem.config.js --env production

# Update environment variables
pm2 restart md-secrets-backend --update-env

# Set environment variables
pm2 set md-secrets-backend:DATABASE_URL "postgresql://prod:pass@localhost:5432/md_linked_secrets"
```

### Using Docker (Optional)
```bash
# Build and run with Docker Compose
docker-compose up -d
```

## 🔍 Troubleshooting

### Common Issues

#### Environment Configuration Issues
```bash
# Check if .env file exists
ls -la backend/.env

# Verify environment variables are loaded
cd backend
python -c "
from app.core.config import settings
print(f'Database URL: {settings.database_url}')
print(f'API Host: {settings.api_host}')
print(f'API Port: {settings.api_port}')
"

# Test database connection with your configured URL
python -c "
from app.core.database import engine
from sqlalchemy import text
import asyncio

async def test_connection():
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT 1'))
        print('✅ Database connection successful!')

asyncio.run(test_connection())
"
```

#### Database Connection Issues
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
psql -h localhost -U your_user -d md_linked_secrets

# Run validation script
./scripts/validate-setup.sh

# Recreate database tables (if needed)
python scripts/setup_database.py

# Check if git tracking fields exist
psql -d md_linked_secrets -c "\d env_exports"
```

#### Database Schema Issues
If you encounter issues with missing tables or columns:

```bash
# Option 1: Use the setup script (recommended)
python scripts/setup_database.py

# Option 2: Manual table recreation
cd backend
python -c "
from app.core.database import engine
from app.models import Base
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print('Database recreated successfully!')
"

# Option 3: Apply git tracking migration only
psql -d md_linked_secrets -f database/add_git_tracking_fields.sql
```

#### Port Conflicts
```bash
# Check if ports are in use
lsof -i :8088  # Backend
lsof -i :3000  # Frontend

# Kill processes if needed
pm2 delete md-secrets-backend
pm2 delete md-secrets-frontend
```

#### CLI Not Found
```bash
# Reinstall CLI
cd cli
pip install -e . --force-reinstall

# Check installation
which lsec
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for the backend
- Frontend powered by [React](https://reactjs.org/) and [Material-UI](https://mui.com/)
- Database management with [SQLAlchemy](https://www.sqlalchemy.org/)
- Process management with [PM2](https://pm2.keymetrics.io/)

---