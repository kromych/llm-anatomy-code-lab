# inventory.ps1 -- list what the tools of "Anatomy of the Open-Source LLM
# Stack" have left on this Windows machine: directories with their sizes,
# credential files (presence only, never contents), processes, listening
# sockets, services, scheduled tasks, Run keys, Startup links, user PATH
# entries, URL handlers and uninstall entries.  Appendix B.
#
#   powershell -File inventory.ps1                  all tools
#   powershell -File inventory.ps1 ollama codex     only these tools
#   powershell -File inventory.ps1 -Remove codex    list, then offer to delete
#                                                   each per-user path, asking
#                                                   every time
# Nothing is deleted unless -Remove is given and you answer "y" for that path.
param([switch]$Remove, [Parameter(ValueFromRemainingArguments)][string[]]$Tools)
$ErrorActionPreference = 'SilentlyContinue'
$U = $env:USERPROFILE; $L = $env:LOCALAPPDATA; $R = $env:APPDATA
$HF = if ($env:HF_HOME) { $env:HF_HOME } else { "$U\.cache\huggingface" }
$All = [ordered]@{
  'llama.cpp' = @{ dirs = @("$L\Programs\llama.cpp", "$L\llama.cpp")
                   proc = 'llama'; ports = @(9931, 8080) }
  'ollama'    = @{ dirs = @("$L\Programs\Ollama", "$L\Ollama", "$U\.ollama")
                   creds = @("$U\.ollama\id_ed25519"); proc = 'ollama'
                   ports = @(11434); name = 'Ollama' }
  # LM Studio on Windows: ~/.lmstudio as on macOS, the application in the
  # per-user Programs directory and its data in %APPDATA% (not observed)
  'lmstudio'  = @{ dirs = @("$U\.lmstudio", "$U\.lmstudio-home-pointer",
                            "$L\Programs\LM Studio", "$R\LM Studio")
                   creds = @("$U\.lmstudio\.internal\lms-key-2")
                   proc = 'llmster|LM Studio'; ports = @(1234, 41343)
                   name = 'LM Studio' }
  'huggingface' = @{ dirs = @("$HF\hub", "$HF\datasets", "$HF\xet")
                     creds = @("$HF\token") }
  'torch'     = @{ dirs = @("$env:TEMP\torchinductor_$env:USERNAME", "$U\.cache\torch",
                            "$U\.triton", "$R\NVIDIA\ComputeCache") }
  'docker'    = @{ dirs = @("$U\.docker", "$L\Docker", "$R\Docker"); proc = 'docker'
                   name = 'Docker' }
  'wsl'       = @{ dirs = @("$L\wsl", "$U\.wslconfig"); proc = 'wsl'; name = 'WSL' }
  'codex'     = @{ dirs = @("$U\.codex"); creds = @("$U\.codex\auth.json"); proc = 'codex'
                   name = 'Codex' }
  'opencode'  = @{ dirs = @("$U\.local\share\opencode", "$U\.config\opencode",
                            "$U\.cache\opencode")
                   creds = @("$U\.local\share\opencode\opencode.db"); proc = 'opencode' }
  'goose'     = @{ dirs = @("$R\Block\goose", "$L\Block\goose"); proc = 'goose' }
  'aider'     = @{ dirs = @("$U\.aider"); creds = @("$U\.aider.conf.yml"); proc = 'aider' }
  'openhands' = @{ dirs = @("$U\.openhands"); creds = @("$U\.openhands\agent_settings.json")
                   proc = 'openhands' }
  # Claude Code: the last two paths are those of the documentation's
  # instructions for removing the native installation (not observed)
  'claude'    = @{ dirs = @("$U\.claude", "$U\.claude.json", "$U\.local\bin\claude.exe",
                            "$U\.local\share\claude")
                   creds = @("$U\.claude\.credentials.json"); proc = 'claude' }
  # Cline's hub daemon listens on 127.0.0.1:25463 until `cline hub stop`
  'cline'     = @{ dirs = @("$U\.cline", "$R\Code\User\globalStorage\saoudrizwan.claude-dev")
                   creds = @("$U\.cline\data\settings\providers.json")
                   proc = 'cline'; ports = @(25463) }
  'python'    = @{ dirs = @("$L\pip\Cache", "$L\uv"); name = '(?!)' }
  # npm's download cache and the packages that npx unpacked
  'node'      = @{ dirs = @("$L\npm-cache\_cacache", "$L\npm-cache\_npx"); name = '(?!)' }
}
if (-not $Tools) { $Tools = $All.Keys }
function Size($p) {
  $i = Get-Item -Force $p
  if (-not $i.PSIsContainer) { return '{0:N1}M' -f ($i.Length / 1MB) }
  '{0:N0}M' -f ((Get-ChildItem -Force -Recurse -File $p | Measure-Object Length -Sum).Sum / 1MB)
}
function Short($p) { $p.Replace($U, '%USERPROFILE%') }
$listen = Get-NetTCPConnection -State Listen
$userPath = (Get-ItemProperty HKCU:\Environment).Path -split ';'
foreach ($t in $Tools) {
  $d = $All[$t]; if (-not $d) { "== $t (unknown)"; continue }
  "== $t"; $mine = @()
  foreach ($p in $d.dirs) { if (Test-Path $p) { '  dir   {0,-7} {1}' -f (Size $p), (Short $p); $mine += $p } }
  foreach ($p in $d.creds) { if (Test-Path $p) { "  cred  present  $(Short $p) (contents not read)" } }
  if ($d.proc) {
    $procs = Get-Process | Where-Object { $_.ProcessName -match $d.proc }
    foreach ($p in $procs) { '  proc  {0,-7} {1}' -f $p.Id, $p.ProcessName }
    $ids = @($procs.Id)
    foreach ($c in $listen | Where-Object { $ids -contains $_.OwningProcess -or $d.ports -contains $_.LocalPort }) {
      "  port  $($c.LocalAddress):$($c.LocalPort) (pid $($c.OwningProcess))" }
  }
  $n = if ($d.name) { $d.name } else { $t }
  Get-Service | Where-Object { $_.Name -match $n -or $_.DisplayName -match $n } |
    ForEach-Object { "  svc   service $($_.Name) ($($_.Status), $($_.StartType))" }
  Get-ScheduledTask | Where-Object { $_.TaskName -match $n } |
    ForEach-Object { "  svc   task $($_.TaskPath)$($_.TaskName) ($($_.State))" }
  foreach ($k in 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run',
                 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run') {
    (Get-ItemProperty $k).PSObject.Properties | Where-Object { $_.Name -match $n } |
      ForEach-Object { "  svc   Run key $k\$($_.Name)" } }
  Get-ChildItem "$R\Microsoft\Windows\Start Menu\Programs\Startup" |
    Where-Object { $_.Name -match $n } | ForEach-Object { "  svc   Startup link $($_.Name)" }
  $userPath | Where-Object { $_ -match $n } | ForEach-Object { "  path  user PATH has $(Short $_)" }
  if (Test-Path "HKCU:\Software\Classes\$t") { "  url   $($t):// handler in HKCU\Software\Classes\$t" }
  Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall',
                'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall' |
    Get-ItemProperty | Where-Object { $_.DisplayName -match $n } |
    ForEach-Object { "  unin  $($_.DisplayName)" }
  if ($Remove) {
    foreach ($p in $mine) {
      $a = Read-Host "delete $(Short $p) ? [y/N]"
      if ($a -eq 'y') { Remove-Item -Recurse -Force $p; '  deleted' } }
  }
}
