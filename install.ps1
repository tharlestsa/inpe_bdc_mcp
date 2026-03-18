#Requires -Version 5.1
<#
.SYNOPSIS
    Instalador inteligente do servidor MCP INPE/Brazil Data Cube para Windows.

.DESCRIPTION
    Automatiza: deteccao/instalacao de Python 3.11+, Git, uv, clonagem do
    repositorio, uv sync e registro no Claude Desktop e/ou Claude Code.

.PARAMETER Uninstall
    Remove a instalacao e as entradas de configuracao MCP.

.PARAMETER InstallDir
    Diretorio de instalacao personalizado (padrao: $HOME\.claude-mcp\inpe-bdc-mcp).

.PARAMETER BdcApiKey
    Chave da API BDC (evita prompt interativo).

.PARAMETER GitRepo
    URL do repositorio Git (padrao: GitHub oficial).

.PARAMETER LocalPath
    Caminho local do projeto — copia em vez de clonar.

.PARAMETER ClaudeDesktop
    Forcar registro no Claude Desktop.

.PARAMETER ClaudeCode
    Forcar registro no Claude Code.

.PARAMETER SkipTests
    Pular execucao de testes apos instalacao.

.PARAMETER Force
    Forcar reinstalacao mesmo se o projeto ja existir.

.EXAMPLE
    .\install.ps1
    .\install.ps1 -BdcApiKey "minha-chave" -ClaudeCode
    .\install.ps1 -LocalPath "C:\src\inpe-bdc-mcp" -SkipTests
    .\install.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [switch]$Uninstall,
    [string]$InstallDir,
    [string]$BdcApiKey,
    [string]$GitRepo = "https://github.com/tharlestsa/inpe_bdc_mcp.git",
    [string]$LocalPath,
    [switch]$ClaudeDesktop,
    [switch]$ClaudeCode,
    [switch]$SkipTests,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ──────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────
$SCRIPT_VERSION   = "1.0.0"
$PROJECT_NAME     = "inpe-bdc-mcp"
$MCP_SERVER_NAME  = "inpe-bdc"
$MIN_PYTHON_MAJOR = 3
$MIN_PYTHON_MINOR = 11
$DEFAULT_INSTALL_DIR = Join-Path $HOME ".claude-mcp\inpe-bdc-mcp"
$CLAUDE_DESKTOP_CONFIG = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
$CLAUDE_CODE_CONFIG    = Join-Path $HOME ".claude\settings.json"

if (-not $InstallDir) { $InstallDir = $DEFAULT_INSTALL_DIR }

# ──────────────────────────────────────────────
# Funcoes de UX
# ──────────────────────────────────────────────
function Write-Banner {
    $banner = @"

  ╔══════════════════════════════════════════════════════════╗
  ║       INPE / Brazil Data Cube — MCP Server              ║
  ║       Instalador Inteligente para Windows                ║
  ║       v$SCRIPT_VERSION                                          ║
  ╚══════════════════════════════════════════════════════════╝

"@
    Write-Host $banner -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Message)
    Write-Host "`n>>> " -ForegroundColor Yellow -NoNewline
    Write-Host $Message -ForegroundColor White
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  [OK] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  [!!] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

function Write-Fail {
    param([string]$Message)
    Write-Host "  [ERRO] " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

function Write-Info {
    param([string]$Message)
    Write-Host "  [i] " -ForegroundColor Cyan -NoNewline
    Write-Host $Message
}

function Write-Summary {
    param([hashtable]$Results)
    Write-Host "`n  ┌─────────────────────────────────────────────┐" -ForegroundColor Cyan
    Write-Host "  │           Resumo da Instalacao               │" -ForegroundColor Cyan
    Write-Host "  ├──────────────┬──────────────────────────────┤" -ForegroundColor Cyan
    foreach ($key in @("Python", "Git", "uv", "Projeto", "Claude Desktop", "Claude Code")) {
        if ($Results.ContainsKey($key)) {
            $val = $Results[$key]
            $color = if ($val -match "^OK") { "Green" } elseif ($val -match "^SKIP|^N/A") { "Yellow" } else { "Red" }
            $keyPad = $key.PadRight(12)
            $valPad = $val.PadRight(28)
            Write-Host "  │ " -ForegroundColor Cyan -NoNewline
            Write-Host "$keyPad" -NoNewline
            Write-Host " │ " -ForegroundColor Cyan -NoNewline
            Write-Host "$valPad" -ForegroundColor $color -NoNewline
            Write-Host " │" -ForegroundColor Cyan
        }
    }
    Write-Host "  └──────────────┴──────────────────────────────┘" -ForegroundColor Cyan
}

# ──────────────────────────────────────────────
# Funcoes utilitarias
# ──────────────────────────────────────────────
function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-CommandExists {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function Update-SessionPath {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath    = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path    = "$userPath;$machinePath"
}

function Invoke-WithRetry {
    param(
        [scriptblock]$ScriptBlock,
        [int]$MaxAttempts = 3,
        [int]$DelaySeconds = 2
    )
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            return & $ScriptBlock
        }
        catch {
            if ($i -eq $MaxAttempts) { throw }
            Write-Warn "Tentativa $i/$MaxAttempts falhou. Retentando em ${DelaySeconds}s..."
            Start-Sleep -Seconds $DelaySeconds
        }
    }
}

function Read-UserChoice {
    param(
        [string]$Prompt,
        [string[]]$ValidChoices,
        [string]$Default
    )
    while ($true) {
        Write-Host "  $Prompt " -NoNewline -ForegroundColor White
        $input_val = Read-Host
        if ([string]::IsNullOrWhiteSpace($input_val) -and $Default) { return $Default }
        if ($ValidChoices -contains $input_val) { return $input_val }
        Write-Warn "Opcao invalida. Escolha entre: $($ValidChoices -join ', ')"
    }
}

function ConvertTo-ForwardSlash {
    param([string]$Path)
    return $Path -replace '\\', '/'
}

function Test-Connectivity {
    param([string]$Url)
    try {
        $request = [System.Net.WebRequest]::Create($Url)
        $request.Timeout = 5000
        if ($env:HTTPS_PROXY -or $env:HTTP_PROXY) {
            $proxyUrl = if ($env:HTTPS_PROXY) { $env:HTTPS_PROXY } else { $env:HTTP_PROXY }
            $request.Proxy = New-Object System.Net.WebProxy($proxyUrl, $true)
        }
        $response = $request.GetResponse()
        $response.Close()
        return $true
    }
    catch {
        return $false
    }
}

# ──────────────────────────────────────────────
# Deteccao de Python
# ──────────────────────────────────────────────
function Find-Python {
    <#
    .SYNOPSIS
        Busca Python >= 3.11 no sistema, filtrando o redirecionamento da Windows Store.
    .OUTPUTS
        Caminho completo do executavel Python ou $null.
    #>
    $candidates = @()

    # 1. Python Launcher (py)
    if (Test-CommandExists "py") {
        try {
            $pyList = & py -0p 2>$null
            foreach ($line in $pyList) {
                if ($line -match "^\s*-V?:?(\d+)\.(\d+)\S*\s+(.+)$") {
                    $major = [int]$Matches[1]
                    $minor = [int]$Matches[2]
                    $path  = $Matches[3].Trim()
                    if ($major -ge $MIN_PYTHON_MAJOR -and $minor -ge $MIN_PYTHON_MINOR) {
                        if ($path -notmatch "WindowsApps") {
                            $candidates += $path
                        }
                    }
                }
            }
        }
        catch { }
    }

    # 2. python / python3 no PATH
    foreach ($cmd in @("python", "python3")) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($found) {
            $p = $found.Source
            if ($p -match "WindowsApps") { continue }
            try {
                $ver = & $p --version 2>&1
                if ($ver -match "Python (\d+)\.(\d+)") {
                    $major = [int]$Matches[1]; $minor = [int]$Matches[2]
                    if ($major -ge $MIN_PYTHON_MAJOR -and $minor -ge $MIN_PYTHON_MINOR) {
                        $candidates += $p
                    }
                }
            }
            catch { }
        }
    }

    # 3. Caminhos comuns
    $commonPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Python313\python.exe"
    )
    foreach ($p in $commonPaths) {
        if (Test-Path $p) {
            try {
                $ver = & $p --version 2>&1
                if ($ver -match "Python (\d+)\.(\d+)") {
                    $major = [int]$Matches[1]; $minor = [int]$Matches[2]
                    if ($major -ge $MIN_PYTHON_MAJOR -and $minor -ge $MIN_PYTHON_MINOR) {
                        $candidates += $p
                    }
                }
            }
            catch { }
        }
    }

    if ($candidates.Count -gt 0) {
        return $candidates[0]
    }
    return $null
}

function Get-PythonVersion {
    param([string]$PythonPath)
    $ver = & $PythonPath --version 2>&1
    if ($ver -match "Python (.+)") { return $Matches[1] }
    return "desconhecida"
}

# ──────────────────────────────────────────────
# Instalacao de dependencias
# ──────────────────────────────────────────────
function Install-PythonIfNeeded {
    $python = Find-Python
    if ($python) {
        $ver = Get-PythonVersion $python
        Write-Ok "Python $ver encontrado em: $python"
        return $python
    }

    Write-Warn "Python >= $MIN_PYTHON_MAJOR.$MIN_PYTHON_MINOR nao encontrado."

    # Tentar via winget
    if (Test-CommandExists "winget") {
        Write-Info "Instalando Python 3.12 via winget..."
        try {
            & winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent 2>&1 | Out-Null
            Update-SessionPath
            $python = Find-Python
            if ($python) {
                $ver = Get-PythonVersion $python
                Write-Ok "Python $ver instalado com sucesso."
                return $python
            }
        }
        catch {
            Write-Warn "Falha na instalacao via winget: $_"
        }
    }

    Write-Fail "Nao foi possivel instalar Python automaticamente."
    Write-Host ""
    Write-Host "  Instale manualmente a partir de:" -ForegroundColor White
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Marque a opcao 'Add Python to PATH' durante a instalacao." -ForegroundColor Yellow
    Write-Host "  Depois, execute este script novamente." -ForegroundColor White
    exit 1
}

function Install-GitIfNeeded {
    if (Test-CommandExists "git") {
        $ver = (& git --version) -replace "git version ", ""
        Write-Ok "Git $ver encontrado."
        return "OK — $ver"
    }

    if ($LocalPath) {
        Write-Info "Git nao encontrado, mas -LocalPath foi fornecido. Continuando..."
        return "SKIP — usando LocalPath"
    }

    Write-Warn "Git nao encontrado."

    if (Test-CommandExists "winget") {
        Write-Info "Instalando Git via winget..."
        try {
            & winget install Git.Git --accept-package-agreements --accept-source-agreements --silent 2>&1 | Out-Null
            Update-SessionPath
            if (Test-CommandExists "git") {
                $ver = (& git --version) -replace "git version ", ""
                Write-Ok "Git $ver instalado com sucesso."
                return "OK — $ver"
            }
        }
        catch {
            Write-Warn "Falha na instalacao via winget: $_"
        }
    }

    Write-Fail "Git necessario para clonar o repositorio."
    Write-Host "  Instale a partir de: https://git-scm.com/download/win" -ForegroundColor Cyan
    Write-Host "  Ou use -LocalPath para apontar para uma copia local." -ForegroundColor Yellow
    exit 1
}

function Install-UvIfNeeded {
    param([string]$PythonPath)

    if (Test-CommandExists "uv") {
        $ver = ((& uv --version) -split " ")[-1]
        Write-Ok "uv $ver encontrado."
        return
    }

    Write-Warn "uv nao encontrado. Instalando..."

    # Metodo 1: script oficial
    try {
        Write-Info "Instalando uv via script oficial..."
        Invoke-WithRetry {
            $installScript = (Invoke-WebRequest -Uri "https://astral.sh/uv/install.ps1" -UseBasicParsing).Content
            Invoke-Expression $installScript 2>&1 | Out-Null
        }
        Update-SessionPath

        # uv instala em $HOME\.local\bin ou $HOME\.cargo\bin
        $uvPaths = @(
            "$HOME\.local\bin",
            "$HOME\.cargo\bin",
            "$env:LOCALAPPDATA\uv"
        )
        foreach ($p in $uvPaths) {
            if (Test-Path "$p\uv.exe") {
                $env:Path = "$p;$env:Path"
                break
            }
        }

        if (Test-CommandExists "uv") {
            $ver = ((& uv --version) -split " ")[-1]
            Write-Ok "uv $ver instalado com sucesso."
            return
        }
    }
    catch {
        Write-Warn "Script oficial falhou: $_"
    }

    # Metodo 2: pip install uv
    try {
        Write-Info "Instalando uv via pip..."
        & $PythonPath -m pip install uv --quiet 2>&1 | Out-Null
        if (Test-CommandExists "uv") {
            $ver = ((& uv --version) -split " ")[-1]
            Write-Ok "uv $ver instalado via pip."
            return
        }
    }
    catch {
        Write-Warn "Falha na instalacao via pip: $_"
    }

    Write-Fail "Nao foi possivel instalar uv."
    Write-Host "  Instale manualmente: https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Cyan
    exit 1
}

# ──────────────────────────────────────────────
# Instalacao do projeto
# ──────────────────────────────────────────────
function Install-Project {
    param([string]$PythonPath)

    # Verificar instalacao existente
    if (Test-Path $InstallDir) {
        if (-not $Force) {
            Write-Warn "Diretorio ja existe: $InstallDir"
            $choice = Read-UserChoice "Deseja [a]tualizar, [r]einstalar ou [c]ancelar? (a/r/c)" @("a","r","c") "a"
            switch ($choice) {
                "a" {
                    Write-Info "Atualizando projeto existente..."
                    Push-Location $InstallDir
                    try {
                        if (Test-Path ".git") {
                            & git pull --ff-only 2>&1 | Out-Null
                        }
                    }
                    finally { Pop-Location }
                }
                "r" {
                    Write-Info "Removendo instalacao anterior..."
                    Remove-Item -Recurse -Force $InstallDir
                }
                "c" {
                    Write-Info "Instalacao cancelada pelo usuario."
                    exit 0
                }
            }
        }
        else {
            Write-Info "Flag -Force: removendo instalacao anterior..."
            Remove-Item -Recurse -Force $InstallDir
        }
    }

    # Criar diretorio pai se necessario
    $parentDir = Split-Path $InstallDir -Parent
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }

    # Clonar ou copiar
    if (-not (Test-Path $InstallDir)) {
        if ($LocalPath) {
            if (-not (Test-Path $LocalPath)) {
                Write-Fail "Caminho local nao encontrado: $LocalPath"
                exit 1
            }
            Write-Info "Copiando projeto de $LocalPath..."
            Copy-Item -Path $LocalPath -Destination $InstallDir -Recurse -Force
            Write-Ok "Projeto copiado."
        }
        else {
            Write-Info "Clonando repositorio..."
            Invoke-WithRetry {
                & git clone $GitRepo $InstallDir 2>&1
                if ($LASTEXITCODE -ne 0) { throw "git clone falhou com exit code $LASTEXITCODE" }
            }
            Write-Ok "Repositorio clonado."
        }
    }

    # Instalar dependencias com uv
    Write-Info "Instalando dependencias (uv sync)..."
    Push-Location $InstallDir
    try {
        $syncResult = & uv sync 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warn "uv sync falhou. Tentando pip install -e ..."
            & $PythonPath -m pip install -e "." --quiet 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Fail "Falha na instalacao das dependencias."
                Write-Host "  Saida: $syncResult" -ForegroundColor Red
                exit 1
            }
            Write-Ok "Dependencias instaladas via pip."
        }
        else {
            Write-Ok "Dependencias instaladas via uv."
        }

        # Validar importacao
        Write-Info "Validando servidor MCP..."
        $validateCmd = "import inpe_bdc_mcp.server; print('OK')"
        $validateResult = & uv run python -c $validateCmd 2>&1
        if ($validateResult -match "OK") {
            Write-Ok "Servidor MCP validado com sucesso."
        }
        else {
            # Fallback: tentar com python direto
            $validateResult = & $PythonPath -c $validateCmd 2>&1
            if ($validateResult -match "OK") {
                Write-Ok "Servidor MCP validado (via python direto)."
            }
            else {
                Write-Warn "Validacao do servidor retornou: $validateResult"
                Write-Warn "O servidor pode nao funcionar corretamente."
            }
        }

        # Testes opcionais
        if (-not $SkipTests) {
            Write-Info "Executando testes..."
            $testResult = & uv run pytest --tb=short -q 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Ok "Testes passaram."
            }
            else {
                Write-Warn "Alguns testes falharam (nao impede a instalacao)."
                Write-Info "Saida dos testes:`n$testResult"
            }
        }
        else {
            Write-Info "Testes pulados (-SkipTests)."
        }
    }
    finally { Pop-Location }
}

# ──────────────────────────────────────────────
# Registro MCP
# ──────────────────────────────────────────────
function Get-McpServerConfig {
    param([string]$PythonPath)

    $uvPath = (Get-Command uv -ErrorAction SilentlyContinue).Source
    if (-not $uvPath) { $uvPath = "uv" }

    $config = @{
        command = ConvertTo-ForwardSlash $uvPath
        args    = @(
            "--directory"
            ConvertTo-ForwardSlash $InstallDir
            "run"
            "inpe-bdc-mcp"
        )
    }

    if ($BdcApiKey) {
        $config.env = @{
            BDC_API_KEY = $BdcApiKey
        }
    }

    return $config
}

function Register-ClaudeDesktop {
    param([hashtable]$ServerConfig)

    $configPath = $CLAUDE_DESKTOP_CONFIG
    $configDir  = Split-Path $configPath -Parent

    if (-not (Test-Path $configDir)) {
        Write-Info "Diretorio do Claude Desktop nao encontrado: $configDir"
        return "N/A — nao instalado"
    }

    # Carregar ou criar configuracao
    $config = @{}
    if (Test-Path $configPath) {
        # Backup
        $backupPath = "$configPath.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item $configPath $backupPath
        Write-Info "Backup criado: $backupPath"

        $raw = Get-Content $configPath -Raw -ErrorAction SilentlyContinue
        if ($raw) {
            try {
                $config = $raw | ConvertFrom-Json -AsHashtable
            }
            catch {
                # PowerShell 5.1 nao suporta -AsHashtable
                $configObj = $raw | ConvertFrom-Json
                $config = @{}
                foreach ($prop in $configObj.PSObject.Properties) {
                    $config[$prop.Name] = $prop.Value
                }
            }
        }
    }

    # Garantir estrutura mcpServers
    if (-not $config.ContainsKey("mcpServers")) {
        $config["mcpServers"] = @{}
    }
    elseif ($config["mcpServers"] -isnot [hashtable]) {
        # Converter PSCustomObject para hashtable
        $servers = @{}
        foreach ($prop in $config["mcpServers"].PSObject.Properties) {
            $servers[$prop.Name] = $prop.Value
        }
        $config["mcpServers"] = $servers
    }

    $config["mcpServers"][$MCP_SERVER_NAME] = $ServerConfig

    $json = $config | ConvertTo-Json -Depth 10
    Set-Content -Path $configPath -Value $json -Encoding UTF8
    Write-Ok "Registrado no Claude Desktop."
    return "OK — $configPath"
}

function Register-ClaudeCode {
    param([hashtable]$ServerConfig)

    $configPath = $CLAUDE_CODE_CONFIG
    $configDir  = Split-Path $configPath -Parent

    if (-not (Test-Path $configDir)) {
        Write-Info "Diretorio do Claude Code nao encontrado: $configDir"
        return "N/A — nao instalado"
    }

    # Carregar ou criar configuracao
    $config = @{}
    if (Test-Path $configPath) {
        # Backup
        $backupPath = "$configPath.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item $configPath $backupPath
        Write-Info "Backup criado: $backupPath"

        $raw = Get-Content $configPath -Raw -ErrorAction SilentlyContinue
        if ($raw) {
            try {
                $config = $raw | ConvertFrom-Json -AsHashtable
            }
            catch {
                $configObj = $raw | ConvertFrom-Json
                $config = @{}
                foreach ($prop in $configObj.PSObject.Properties) {
                    $config[$prop.Name] = $prop.Value
                }
            }
        }
    }

    # Claude Code usa estrutura "mcpServers" no settings.json
    if (-not $config.ContainsKey("mcpServers")) {
        $config["mcpServers"] = @{}
    }
    elseif ($config["mcpServers"] -isnot [hashtable]) {
        $servers = @{}
        foreach ($prop in $config["mcpServers"].PSObject.Properties) {
            $servers[$prop.Name] = $prop.Value
        }
        $config["mcpServers"] = $servers
    }

    $config["mcpServers"][$MCP_SERVER_NAME] = $ServerConfig

    $json = $config | ConvertTo-Json -Depth 10
    Set-Content -Path $configPath -Value $json -Encoding UTF8
    Write-Ok "Registrado no Claude Code."
    return "OK — $configPath"
}

function Register-McpServer {
    param([string]$PythonPath)

    $serverConfig = Get-McpServerConfig -PythonPath $PythonPath
    $results = @{}

    # Solicitar BDC_API_KEY se nao fornecida
    if (-not $BdcApiKey) {
        Write-Host ""
        Write-Host "  A API BDC aceita uma chave opcional para acesso a recursos protegidos." -ForegroundColor White
        Write-Host "  Pressione Enter para pular (acesso publico sera utilizado)." -ForegroundColor Gray
        Write-Host "  BDC_API_KEY: " -NoNewline -ForegroundColor White
        $key = Read-Host
        if ($key) {
            $BdcApiKey = $key
            $serverConfig.env = @{ BDC_API_KEY = $BdcApiKey }
        }
    }

    # Detectar alvos de registro
    $registerDesktop = $ClaudeDesktop -or (-not $ClaudeDesktop -and -not $ClaudeCode)
    $registerCode    = $ClaudeCode    -or (-not $ClaudeDesktop -and -not $ClaudeCode)

    if ($registerDesktop) {
        $results["Claude Desktop"] = Register-ClaudeDesktop -ServerConfig $serverConfig
    }
    else {
        $results["Claude Desktop"] = "SKIP — nao solicitado"
    }

    if ($registerCode) {
        $results["Claude Code"] = Register-ClaudeCode -ServerConfig $serverConfig
    }
    else {
        $results["Claude Code"] = "SKIP — nao solicitado"
    }

    return $results
}

# ──────────────────────────────────────────────
# Desinstalacao
# ──────────────────────────────────────────────
function Invoke-Uninstall {
    Write-Step "Desinstalando $PROJECT_NAME..."

    # Remover entrada do Claude Desktop
    if (Test-Path $CLAUDE_DESKTOP_CONFIG) {
        try {
            $raw = Get-Content $CLAUDE_DESKTOP_CONFIG -Raw
            try {
                $config = $raw | ConvertFrom-Json -AsHashtable
            }
            catch {
                $configObj = $raw | ConvertFrom-Json
                $config = @{}
                foreach ($prop in $configObj.PSObject.Properties) {
                    $config[$prop.Name] = $prop.Value
                }
            }

            if ($config.ContainsKey("mcpServers")) {
                $servers = $config["mcpServers"]
                if ($servers -isnot [hashtable]) {
                    $ht = @{}
                    foreach ($prop in $servers.PSObject.Properties) { $ht[$prop.Name] = $prop.Value }
                    $servers = $ht
                    $config["mcpServers"] = $servers
                }
                if ($servers.ContainsKey($MCP_SERVER_NAME)) {
                    $servers.Remove($MCP_SERVER_NAME)
                    $json = $config | ConvertTo-Json -Depth 10
                    Set-Content -Path $CLAUDE_DESKTOP_CONFIG -Value $json -Encoding UTF8
                    Write-Ok "Entrada removida do Claude Desktop."
                }
                else {
                    Write-Info "Entrada nao encontrada no Claude Desktop."
                }
            }
        }
        catch {
            Write-Warn "Falha ao processar configuracao do Claude Desktop: $_"
        }
    }

    # Remover entrada do Claude Code
    if (Test-Path $CLAUDE_CODE_CONFIG) {
        try {
            $raw = Get-Content $CLAUDE_CODE_CONFIG -Raw
            try {
                $config = $raw | ConvertFrom-Json -AsHashtable
            }
            catch {
                $configObj = $raw | ConvertFrom-Json
                $config = @{}
                foreach ($prop in $configObj.PSObject.Properties) {
                    $config[$prop.Name] = $prop.Value
                }
            }

            if ($config.ContainsKey("mcpServers")) {
                $servers = $config["mcpServers"]
                if ($servers -isnot [hashtable]) {
                    $ht = @{}
                    foreach ($prop in $servers.PSObject.Properties) { $ht[$prop.Name] = $prop.Value }
                    $servers = $ht
                    $config["mcpServers"] = $servers
                }
                if ($servers.ContainsKey($MCP_SERVER_NAME)) {
                    $servers.Remove($MCP_SERVER_NAME)
                    $json = $config | ConvertTo-Json -Depth 10
                    Set-Content -Path $CLAUDE_CODE_CONFIG -Value $json -Encoding UTF8
                    Write-Ok "Entrada removida do Claude Code."
                }
                else {
                    Write-Info "Entrada nao encontrada no Claude Code."
                }
            }
        }
        catch {
            Write-Warn "Falha ao processar configuracao do Claude Code: $_"
        }
    }

    # Remover diretorio do projeto
    if (Test-Path $InstallDir) {
        Remove-Item -Recurse -Force $InstallDir
        Write-Ok "Diretorio removido: $InstallDir"
    }
    else {
        Write-Info "Diretorio nao encontrado: $InstallDir"
    }

    Write-Host ""
    Write-Ok "Desinstalacao concluida."
    Write-Info "Python, Git e uv nao foram removidos (sao ferramentas compartilhadas)."
}

# ──────────────────────────────────────────────
# Funcao principal
# ──────────────────────────────────────────────
function Invoke-Main {
    Write-Banner

    # Desinstalacao
    if ($Uninstall) {
        Invoke-Uninstall
        return
    }

    $summary = @{}

    # ── Pre-verificacoes ──
    Write-Step "Pre-verificacoes"

    # Versao do Windows
    $osInfo = [System.Environment]::OSVersion
    Write-Info "Sistema: Windows $($osInfo.Version)"

    # Administrador
    if (Test-IsAdmin) {
        Write-Info "Executando como Administrador."
    }
    else {
        Write-Info "Executando sem privilegios de Administrador (ok para a maioria dos casos)."
    }

    # Execution Policy
    $execPolicy = Get-ExecutionPolicy -Scope CurrentUser
    if ($execPolicy -eq "Restricted") {
        Write-Warn "Execution Policy esta como 'Restricted'."
        Write-Host "  Execute antes: " -ForegroundColor Yellow -NoNewline
        Write-Host "Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned" -ForegroundColor Cyan
    }

    # Proxy
    if ($env:HTTPS_PROXY -or $env:HTTP_PROXY) {
        $proxyUrl = if ($env:HTTPS_PROXY) { $env:HTTPS_PROXY } else { $env:HTTP_PROXY }
        Write-Info "Proxy detectado: $proxyUrl"
    }

    # Conectividade
    Write-Info "Testando conectividade..."
    if (Test-Connectivity "https://github.com") {
        Write-Ok "GitHub acessivel."
    }
    else {
        Write-Warn "GitHub inacessivel. Verifique sua conexao ou proxy."
        if (-not $LocalPath) {
            Write-Fail "Conexao com GitHub necessaria para clonar o repositorio. Use -LocalPath para instalacao offline."
            exit 1
        }
    }

    if (Test-Connectivity "https://data.inpe.br") {
        Write-Ok "INPE STAC API acessivel."
    }
    else {
        Write-Warn "INPE STAC API inacessivel. O servidor funcionara, mas pode falhar em tempo de execucao."
    }

    # ── Python ──
    Write-Step "Python (>= $MIN_PYTHON_MAJOR.$MIN_PYTHON_MINOR)"
    $pythonPath = Install-PythonIfNeeded
    $pythonVer  = Get-PythonVersion $pythonPath
    $summary["Python"] = "OK — $pythonVer"

    # ── Git ──
    Write-Step "Git"
    $summary["Git"] = Install-GitIfNeeded

    # ── uv ──
    Write-Step "uv (gerenciador de pacotes)"
    Install-UvIfNeeded -PythonPath $pythonPath
    $uvVer = ((& uv --version) -split " ")[-1]
    $summary["uv"] = "OK — $uvVer"

    # ── Projeto ──
    Write-Step "Projeto $PROJECT_NAME"
    Install-Project -PythonPath $pythonPath
    $summary["Projeto"] = "OK — $InstallDir"

    # ── Registro MCP ──
    Write-Step "Registro MCP"
    $mcpResults = Register-McpServer -PythonPath $pythonPath
    foreach ($key in $mcpResults.Keys) {
        $summary[$key] = $mcpResults[$key]
    }

    # ── Resumo ──
    Write-Summary -Results $summary

    Write-Host ""
    Write-Host "  Para testar a instalacao:" -ForegroundColor White
    Write-Host "    1. Abra (ou reinicie) o Claude Desktop ou Claude Code" -ForegroundColor Gray
    Write-Host "    2. No Claude Code, execute: " -ForegroundColor Gray -NoNewline
    Write-Host "/mcp" -ForegroundColor Cyan -NoNewline
    Write-Host " e verifique se '$MCP_SERVER_NAME' aparece na lista" -ForegroundColor Gray
    Write-Host "    3. Teste com: " -ForegroundColor Gray -NoNewline
    Write-Host '"Liste as colecoes do Brazil Data Cube"' -ForegroundColor Cyan
    Write-Host ""
}

# ──────────────────────────────────────────────
# Ponto de entrada
# ──────────────────────────────────────────────
Invoke-Main
