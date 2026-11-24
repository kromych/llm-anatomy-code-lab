# check.ps1 -- compare installed tool versions with the pins in versions.csv
# (Appendix A).  Read-only.  Run with
#   powershell -ExecutionPolicy Bypass -File check.ps1
param([string]$Csv = (Join-Path $PSScriptRoot 'versions.csv'))
'{0,-38} {1,-10} {2,-10} {3}' -f 'tool', 'pinned', 'found', 'status'
foreach ($r in Import-Csv $Csv) {
  if (-not $r.windows) { continue }
  $out = ''
  # the redirection must be inside the expression to catch native stderr
  try { $out = (Invoke-Expression ($r.windows + ' 2>&1') | Out-String) } catch { }
  $pat = if ($r.pattern) { $r.pattern } else { '[0-9]+(\.[0-9]+)+' }
  $m = [regex]::Match($out, $pat)
  $want = $r.pinned -replace '[^0-9.]', ''
  if (-not $m.Success) { $ver = '-'; $status = 'missing' }
  else {
    $ver = $m.Value -replace '[^0-9.]', ''
    $status = if ($ver -eq $want) { 'ok' } else { 'differs' }
  }
  '{0,-38} {1,-10} {2,-10} {3}' -f $r.tool, $r.pinned, $ver, $status
}
