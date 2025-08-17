module.exports = {
  apps: [{
    name: 'money-api',
    script: 'uvicorn',
    args: 'main:app --host 0.0.0.0 --port 8000 --workers 4',
    cwd: './backend',
    instances: 1,
    exec_mode: 'fork',
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PORT: 8000,
      PYTHONPATH: '/home/ubuntu/calculadoravix'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true,
    autorestart: true,
    max_restarts: 10,
    min_uptime: '10s'
  }]
};