param(
    [int]$Port = 3307
)

$ErrorActionPreference = "Stop"

$RuntimeDir = Join-Path $env:ProgramData "CodexBlog"
$ConfigFile = Join-Path $RuntimeDir "my.ini"
$BaseDir = if ($env:MYSQL_BASE_DIR) { $env:MYSQL_BASE_DIR } else { "E:\MySQL\MySQL Server 8.0" }
$Mysqld = Join-Path $BaseDir "bin\mysqld.exe"

& $Mysqld --defaults-file="$ConfigFile" --console

