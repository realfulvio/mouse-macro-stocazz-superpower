<#
 Inventario di un pacchetto: dimensione, SHA-256, firma Authenticode, versione, Mark-of-the-Web.
 Uso:  .\inventory.ps1 -Path C:\bench\dl\* -Out data\inventory.csv
 Gli hash servono per la ricerca su VirusTotal (vt_lookup.py) e per rendere verificabile cosa e' stato installato.
#>
param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Out)
Get-ChildItem $Path -File | ForEach-Object {
  $sig = Get-AuthenticodeSignature $_.FullName
  [pscustomobject]@{
    file = $_.Name; bytes = $_.Length; mb = [math]::Round($_.Length / 1MB, 3)
    sha256 = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    version = $_.VersionInfo.FileVersion; signed = $sig.Status; signer = $sig.SignerCertificate.Subject
    motw = [bool](Get-Content "$($_.FullName):Zone.Identifier" -ErrorAction SilentlyContinue)
  }
} | Export-Csv -NoTypeInformation -Encoding UTF8 $Out
Import-Csv $Out | Format-Table -AutoSize
