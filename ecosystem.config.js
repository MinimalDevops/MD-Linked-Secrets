module.exports = {
  apps: [
    {
      name: 'md-secrets-backend',
      script: 'backend/main.py',
      interpreter: 'python',
      args: '-m uvicorn main:app --host 0.0.0.0 --port 8088',
      cwd: './',
      env: {
        NODE_ENV: 'production',
        DATABASE_URL: 'postgresql://username:password@localhost:5432/md_linked_secrets',
        SECRET_KEY: 'your-secret-key-here',
        ENCRYPTION_KEY: 'your-encryption-key-here-32-characters-long'
      },
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      log_file: './logs/backend.log',
      time: true,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    },
    {
      name: 'md-secrets-frontend',
      script: 'npm',
      args: 'start',
      cwd: './frontend',
      env: {
        NODE_ENV: 'production',
        REACT_APP_API_URL: 'http://localhost:8088',
        PORT: 3000
      },
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      log_file: './logs/frontend.log',
      time: true,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    }
  ]
};
