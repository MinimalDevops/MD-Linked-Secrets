module.exports = {
  apps: [
    {
      name: 'md-secrets-frontend',
      script: 'npm',
      args: 'start',
      cwd: './frontend',
      instances: 1,
      autorestart: true,
      watch: false, // React has its own hot reload
      env: {
        NODE_ENV: 'development',
        PORT: '3030',
        BROWSER: 'none', // Prevent auto-opening browser
        GENERATE_SOURCEMAP: 'false' // Faster builds
      },
      max_memory_restart: '800M',
      log_file: './logs/frontend.log',
      out_file: './logs/frontend-out.log',
      error_file: './logs/frontend-error.log',
      time: true,
      merge_logs: true,
      restart_delay: 2000,
      min_uptime: '10s',
      max_restarts: 5
    }
  ]
}; 