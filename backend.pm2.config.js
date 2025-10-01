module.exports = {
  apps: [
    {
      name: 'md-secrets-backend',
      script: './start-backend.sh',
      cwd: './',
      interpreter: 'bash',
      env: {
        NODE_ENV: 'production'
      },
      instances: 1,
      autorestart: true,
      // watch: ['./backend/app'],  // Disabled for production
      ignore_watch: ['node_modules', '*.log', '__pycache__', '.pytest_cache', '*.pyc'],
      max_memory_restart: '500M',
      log_file: './logs/backend.log',
      out_file: './logs/backend-out.log',
      error_file: './logs/backend-error.log',
      time: true,
      merge_logs: true,
      restart_delay: 1000,
      min_uptime: '10s',
      max_restarts: 10
    }
  ]
}; 