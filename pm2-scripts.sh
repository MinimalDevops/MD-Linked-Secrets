#!/bin/bash

# PM2 Management Scripts for MD-Linked-Secrets
# Make sure logs directory exists
mkdir -p logs

echo "🚀 MD-Linked-Secrets PM2 Management"
echo "=================================="

case "$1" in
  "start-backend")
    echo "🔧 Starting Backend..."
    pm2 start backend.pm2.config.js
    echo "✅ Backend started! Use 'pm2 logs md-secrets-backend' to view logs"
    ;;
    
  "start-frontend")
    echo "🎨 Starting Frontend..."
    pm2 start frontend.pm2.config.js
    echo "✅ Frontend started! Use 'pm2 logs md-secrets-frontend' to view logs"
    ;;
    
  "start-all")
    echo "🚀 Starting Backend and Frontend..."
    pm2 start backend.pm2.config.js
    pm2 start frontend.pm2.config.js
    echo "✅ Both services started!"
    pm2 status
    ;;
    
  "stop-backend")
    echo "🛑 Stopping Backend..."
    pm2 stop md-secrets-backend
    ;;
    
  "stop-frontend")
    echo "🛑 Stopping Frontend..."
    pm2 stop md-secrets-frontend
    ;;
    
  "stop-all")
    echo "🛑 Stopping all services..."
    pm2 stop md-secrets-backend md-secrets-frontend
    ;;
    
  "restart-backend")
    echo "🔄 Restarting Backend..."
    pm2 restart md-secrets-backend
    ;;
    
  "restart-frontend")
    echo "🔄 Restarting Frontend..."
    pm2 restart md-secrets-frontend
    ;;
    
  "restart-all")
    echo "🔄 Restarting all services..."
    pm2 restart md-secrets-backend md-secrets-frontend
    ;;
    
  "status")
    echo "📊 Service Status:"
    pm2 status
    ;;
    
  "logs")
    echo "📋 Showing logs for all services..."
    pm2 logs
    ;;
    
  "logs-backend")
    echo "📋 Backend logs:"
    pm2 logs md-secrets-backend
    ;;
    
  "logs-frontend")
    echo "📋 Frontend logs:"
    pm2 logs md-secrets-frontend
    ;;
    
  "delete-all")
    echo "🗑️  Deleting all PM2 processes..."
    pm2 delete md-secrets-backend md-secrets-frontend
    ;;
    
  "monitor")
    echo "📈 Opening PM2 Monitor..."
    pm2 monit
    ;;
    
  *)
    echo "Usage: $0 {start-backend|start-frontend|start-all|stop-backend|stop-frontend|stop-all|restart-backend|restart-frontend|restart-all|status|logs|logs-backend|logs-frontend|delete-all|monitor}"
    echo ""
    echo "Examples:"
    echo "  $0 start-all          # Start both backend and frontend"
    echo "  $0 restart-backend    # Restart only backend"
    echo "  $0 logs-frontend      # View frontend logs"
    echo "  $0 status             # Show status of all processes"
    echo "  $0 monitor            # Open PM2 monitoring dashboard"
    exit 1
    ;;
esac 