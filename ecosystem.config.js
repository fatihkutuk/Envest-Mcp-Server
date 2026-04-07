module.exports = {
  apps: [
    {
      name: "envest-mcp",
      script: "-m",
      args: "scada_mcp.combined --host 127.0.0.1 --port 8001 --require-token",
      interpreter: "python3",
      cwd: "/home/envest-mcp/htdocs/mcp.envest.com.tr/mcps/scada",
      env: {
        LOG_LEVEL: "info",
      },
      // Auto-restart
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
      // Logging
      error_file: "/home/envest-mcp/htdocs/mcp.envest.com.tr/logs/error.log",
      out_file: "/home/envest-mcp/htdocs/mcp.envest.com.tr/logs/out.log",
      merge_logs: true,
      log_date_format: "YYYY-MM-DD HH:mm:ss",
    },
  ],
};
