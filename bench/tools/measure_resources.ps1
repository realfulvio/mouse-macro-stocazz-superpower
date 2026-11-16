<#
 Campiona CPU e RAM di un processo (e dei suoi figli) ogni secondo -> CSV.
 CPU = % di UN core (delta tempo CPU / delta tempo reale), come nelle misure di progetto; RAM = Private Bytes e Working Set.
 Uso:  .\measure_resources.ps1 -Name "TinyTask" -Seconds 60 -Out data\tinytask\idle_01.csv
 Per l'analisi a eventi (ETW/WPA): vedi bench\PROCEDURA.md, sezione "Profilo ETW opzionale".
#>
param([Parameter(Mandatory)][string]$Name, [int]$Seconds = 60, [Parameter(Mandatory)][string]$Out, [int]$IntervalMs = 1000)
$ErrorActionPreference = 'Stop'
function Get-Tree($rootIds) {
  $all = Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId
  $set = [System.Collections.Generic.HashSet[int]]::new(); $rootIds | ForEach-Object { [void]$set.Add($_) }
  do { $n = $set.Count
       foreach ($p in $all) { if ($set.Contains([int]$p.ParentProcessId)) { [void]$set.Add([int]$p.ProcessId) } }
  } while ($set.Count -ne $n)
  $set
}
$roots = (Get-Process -Name $Name -ErrorAction Stop).Id
$rows = New-Object System.Collections.Generic.List[object]
$prevCpu = $null; $prevT = $null
$sw = [Diagnostics.Stopwatch]::StartNew()
while ($sw.Elapsed.TotalSeconds -lt $Seconds) {
  $ids = Get-Tree $roots
  $procs = foreach ($id in $ids) { Get-Process -Id $id -ErrorAction SilentlyContinue }
  $cpuSec = 0.0; foreach ($p in $procs) { try { $cpuSec += $p.TotalProcessorTime.TotalSeconds } catch {} }
  $t = $sw.Elapsed.TotalSeconds
  $pct = if ($null -ne $prevCpu -and $t -gt $prevT) { 100.0 * ($cpuSec - $prevCpu) / ($t - $prevT) } else { $null }
  $priv = ($procs | Measure-Object PrivateMemorySize64 -Sum).Sum / 1MB
  $ws = ($procs | Measure-Object WorkingSet64 -Sum).Sum / 1MB
  $h = ($procs | Measure-Object HandleCount -Sum).Sum
  $rows.Add([pscustomobject]@{ t_s = [math]::Round($t,2); cpu_pct_of_core = $pct; private_mb = [math]::Round($priv,2); workingset_mb = [math]::Round($ws,2); handles = $h; procs = @($procs).Count })
  $prevCpu = $cpuSec; $prevT = $t
  Start-Sleep -Milliseconds $IntervalMs
}
New-Item -ItemType Directory -Force -Path (Split-Path $Out) | Out-Null
$rows | Export-Csv -NoTypeInformation -Encoding UTF8 $Out
$v = $rows | Where-Object { $null -ne $_.cpu_pct_of_core }
"{0}: CPU medio {1:N1}% di un core, mediana {2:N1}% | Private max {3:N1} MB" -f $Name, ($v | Measure-Object cpu_pct_of_core -Average).Average, ($v.cpu_pct_of_core | Sort-Object)[[int]($v.Count/2)], ($rows | Measure-Object private_mb -Maximum).Maximum
