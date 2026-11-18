$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$src = "$env:LOCALAPPDATA\Programs\llama.cpp"
$W = "$env:USERPROFILE\isa-bench"
$VD = "$env:LOCALAPPDATA\isa-bench"
$M = "$env:USERPROFILE\models\gemma-3-1b-it"
$models = "$M\google_gemma-3-1b-it-Q4_0.gguf,$M\google_gemma-3-1b-it-Q8_0.gguf,$M\google_gemma-3-1b-it-Q4_K_M.gguf"
$HV = '\Hyper-V Hypervisor Logical Processor(_Total)\% Total Run Time'
New-Item -ItemType Directory -Force "$W\out","$VD" | Out-Null
Set-Content "$W\empty.txt" ""
function Log($m) { $l = "{0} {1}" -f (Get-Date -Format o), $m; $l; Add-Content "$W\driver.log" $l }
function Total($s) { (Get-Counter $HV -SampleInterval $s -MaxSamples 1).CounterSamples[0].CookedValue }
function LaneBusy {   # badc lane marker, honoured only while its recorded process lives (as lane_guard.py does)
  $f = 'R:\src\compilers\badc\.gate-lane'
  if (!(Test-Path $f)) { return $false }
  $id = 0; [int]::TryParse(((Get-Content $f -Raw).Trim() -split ' ')[0], [ref]$id) | Out-Null
  return [bool](Get-Process -Id $id -ErrorAction SilentlyContinue)
}
function Others { (@(Get-Process cargo,rustc,badc*,llama-*,link,cl,clang* -ErrorAction SilentlyContinue).Name | Sort-Object -Unique) -join ',' }
function WaitIdle {
  $ok = 0
  for ($i = 0; $i -lt 3600; $i++) {
    $b = Total 3; $o = Others; $l = LaneBusy
    if ($b -lt 5 -and -not $o -and -not $l) { $ok++; if ($ok -ge 2) { return ("idle check: busy={0:N1}% after {1}s" -f $b, ($i * 3)) } } else { $ok = 0 }
  }
  return ("idle check: GAVE UP busy={0:N1}% others={1} lane={2}" -f $b, $o, $l)
}
function RunMon($exe, $argList, $out, $err, $intf) {
  $p = Start-Process -FilePath $exe -ArgumentList $argList -RedirectStandardOutput $out -RedirectStandardError $err -RedirectStandardInput "$W\empty.txt" -NoNewWindow -PassThru
  $null = $p.Handle
  $prev = @{}; foreach ($q in Get-Process) { $prev[$q.Id] = $q.TotalProcessorTime.TotalSeconds }
  $t0 = Get-Date
  while (-not $p.HasExited) {
    $tot = Total 5
    $t1 = Get-Date; $dt = ($t1 - $t0).TotalSeconds; $t0 = $t1
    $lines = @()
    foreach ($q in Get-Process) {
      $c = $q.TotalProcessorTime.TotalSeconds
      if ($c -eq $null) { continue }
      $pc = 0; if ($prev.ContainsKey($q.Id)) { $pc = $prev[$q.Id] }
      $d = ($c - $pc) / $dt; $prev[$q.Id] = $c
      if ($q.Id -ne $p.Id -and $q.Name -ne 'Idle' -and $d -gt 0.2) { $lines += ("{0} {1} {2} {3:N2}" -f (Get-Date -Format T), $q.Id, $q.Name, $d) }
    }
    $lines += ("{0} 0 TOTAL% {1:N1}" -f (Get-Date -Format T), $tot)
    Add-Content $intf $lines
  }
  $p.WaitForExit()
  return $p.ExitCode
}
function BenchOnce($label, $dir, $t, $extra) {
  $o = "$W\out\$label"
  "label=$label dir=$dir threads=$t extra=$extra" | Set-Content "$o.env"
  WaitIdle | Add-Content "$o.env"
  "start $(Get-Date -Format o)" | Add-Content "$o.env"
  $p0 = Start-Process "$dir\llama-completion.exe" "-m $M\google_gemma-3-1b-it-Q4_0.gguf -p Hello -n 1 -no-cnv -t $t --temp 0" -RedirectStandardOutput "$o.completion.out" -RedirectStandardError "$o.completion.log" -RedirectStandardInput "$W\empty.txt" -NoNewWindow -Wait -PassThru
  Set-Content "$o.interference" @()
  Log "bench $label start"
  $rc = RunMon "$dir\llama-bench.exe" "-m $models -p 512 -n 128 -r 5 -t $t -o csv -oe md $extra" "$o.csv" "$o.stderr" "$o.interference"
  Get-Content "$o.stderr" | Where-Object { $_ -like '|*' } | Set-Content "$o.md"
  "rc=$rc completion_rc=$($p0.ExitCode) end $(Get-Date -Format o)" | Add-Content "$o.env"
  $bad = @(Get-Content "$o.interference" | Where-Object {
      $f = $_ -split ' '
      ($f[2] -eq 'TOTAL%' -and [double]$f[3] -gt 70) -or ($f[2] -ne 'TOTAL%' -and $f[2] -notin 'System','Registry','Memory Compression' -and [double]$f[3] -ge 0.5) }).Count
  Log "bench $label rc=$rc interference_samples=$bad"
  return ($bad -eq 0)
}
function Bench($label, $dir, $t, $extra) {
  if (Test-Path "$W\out\$label.done") { Log "skip $label (done)"; return }
  for ($a = 1; $a -le 3; $a++) {
    if (BenchOnce $label $dir $t $extra) { Set-Content "$W\out\$label.done" "attempt $a"; return }
    if ($a -lt 3) { Get-ChildItem "$W\out\$label.*" | Where-Object { $_.Name -notmatch '\.try\d\.' } | ForEach-Object { Move-Item $_.FullName ($_.FullName -replace "\\$([regex]::Escape($label))\.", "\$label.try$a.") -Force } }
  }
  Set-Content "$W\out\$label.done" "attempt 3 (all attempts disturbed)"
}
& {
  Get-Date -Format o
  (Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber | Format-List | Out-String).Trim()
  (Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed | Format-List | Out-String).Trim()
  powercfg /getactivescheme
  cmd /c "`"$src\llama-bench.exe`" --version 2>&1"
} | Set-Content "$W\system.txt"
$variants = 'x64','sse42','sandybridge','ivybridge','piledriver','haswell'
foreach ($var in $variants) {
  $stray = "$env:USERPROFILE\$var"   # left by an earlier attempt that resolved the copy path relative to the home folder
  if ((Test-Path $stray) -and (@(Get-ChildItem $stray -Force).Name -join ',') -eq "llama-$var") { Remove-Item $stray -Recurse -Force; Log "removed stray $stray" }
  $d = "$VD\llama-$var"
  if (!(Test-Path $d)) {
    New-Item -ItemType Directory -Force $d | Out-Null
    Get-ChildItem $src -File | Where-Object { $_.Name -notlike 'ggml-cpu-*.dll' } | Copy-Item -Destination $d
    Copy-Item "$src\ggml-cpu-$var.dll" $d
  }
  Log ("copy {0}: {1} files, cpu dll: {2}" -f $d, (Get-ChildItem $d -File).Count, ((Get-ChildItem $d -Filter 'ggml-cpu-*.dll').Name -join ','))
}
$p0 = Start-Process "$src\llama-completion.exe" "-m $M\google_gemma-3-1b-it-Q4_0.gguf -p Hello -n 1 -no-cnv -t 8 --temp 0 -v" -RedirectStandardOutput "$W\out\default.completion.out" -RedirectStandardError "$W\out\default.completion.log" -RedirectStandardInput "$W\empty.txt" -NoNewWindow -Wait -PassThru
foreach ($var in $variants) {
  if ($var -eq 'haswell') { Bench "$var-t8" "$VD\llama-$var" 8 "--repack 1,0" } else { Bench "$var-t8" "$VD\llama-$var" 8 "" }
}
Log "ALL DONE"
