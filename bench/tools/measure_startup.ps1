<#
 Tempo di avvio: dal CreateProcess alla prima finestra principale visibile E che risponde. N ripetizioni -> CSV.
 La prima (fredda) e' marcata cold=1; le altre sono "calde" (file in cache): riportale separate.
 Uso:  .\measure_startup.ps1 -Exe "C:\bench\tinytask\tinytask.exe" -ProcName tinytask -Runs 30 -Out data\tinytask\startup.csv
 Se l'app parte nel tray senza finestra usa -TimeoutS e leggi la colonna ok=0: NON inventare un tempo.
#>
param([Parameter(Mandatory)][string]$Exe, [Parameter(Mandatory)][string]$ProcName, [int]$Runs = 30,
      [Parameter(Mandatory)][string]$Out, [int]$TimeoutS = 20, [string]$ArgumentList = "")
Add-Type -Namespace W -Name U -MemberDefinition '[DllImport("user32.dll")] public static extern bool IsWindowVisible(System.IntPtr h);'
$rows = @()
for ($i = 1; $i -le $Runs; $i++) {
  Get-Process -Name $ProcName -ErrorAction SilentlyContinue | Stop-Process -Force; Start-Sleep -Milliseconds 800
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $p = if ($ArgumentList) { Start-Process -FilePath $Exe -ArgumentList $ArgumentList -PassThru } else { Start-Process -FilePath $Exe -PassThru }
  $ok = 0
  while ($sw.Elapsed.TotalSeconds -lt $TimeoutS) {
    $q = Get-Process -Name $ProcName -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 -and [W.U]::IsWindowVisible($_.MainWindowHandle) -and $_.Responding } | Select-Object -First 1
    if ($q) { $ok = 1; break }
    Start-Sleep -Milliseconds 5
  }
  $rows += [pscustomobject]@{ run = $i; cold = [int]($i -eq 1); ok = $ok; startup_s = [math]::Round($sw.Elapsed.TotalSeconds, 3) }
}
Get-Process -Name $ProcName -ErrorAction SilentlyContinue | Stop-Process -Force
New-Item -ItemType Directory -Force -Path (Split-Path $Out) | Out-Null
$rows | Export-Csv -NoTypeInformation -Encoding UTF8 $Out
$w = ($rows | Where-Object { $_.ok -eq 1 -and $_.cold -eq 0 }).startup_s | Sort-Object
if ($w) { "{0}: avvio caldo mediana {1:N3}s, p95 {2:N3}s su {3} avvii" -f $ProcName, $w[[int]($w.Count/2)], $w[[math]::Min($w.Count-1,[int][math]::Ceiling($w.Count*0.95)-1)], $w.Count }
