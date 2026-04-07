module.exports = {
  apps: [{
    name: "envest-mcp",
    script: "python3",
    args: "-m scada_mcp.combined --host 127.0.0.1 --port 8001 --require-token",
    cwd: "/home/envest-mcp/htdocs/mcp.envest.com.tr/mcps/scada",
    interpreter: "none",
    env: { LOG_LEVEL: "info" },
    autorestart: true,
    max_restarts: 10,
    restart_delay: 3000,
    error_file: "/home/envest-mcp/htdocs/mcp.envest.com.tr/logs/error.log",
    out_file: "/home/envest-mcp/htdocs/mcp.envest.com.tr/logs/out.log",
    merge_logs: true,
    log_date_format: "YYYY-MM-DD HH:mm:ss",
  }],
};
