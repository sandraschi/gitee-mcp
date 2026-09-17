# Per-repo fleet start config for gitee-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'gitee-mcp'
    BackendPort  = 11161
    FrontendPort = 11162
    HealthPath   = '/api/health'
    WebRoot      = 'webapp'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'gitee_mcp.server:app'
        Env           = @{ WEB_PORT = '11161' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'bun'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
