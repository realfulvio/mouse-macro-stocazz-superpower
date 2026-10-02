
## Variante diagnostica per compatibilita Windows

Dopo aver ottenuto la portable, trasformarla senza ricompilare il runtime:

```powershell
python build_compatibility.py --portable dist/windows/MouseMacroStocazzSuperpower-Windows-Portable.zip --output dist/windows/MouseMacroStocazzSuperpower-Windows-Compatibility-Candidate.zip
```

Il tool conserva i binari Python e le dipendenze byte per byte, mantiene il nome originale pythonw.exe, elimina app/sitecustomize.py e aggiunge launcher .cmd IT/EN. Conservare il pacchetto principale come input separato. La variante e diagnostica: la firma PSF autentica il runtime, non certifica i sorgenti dell'app e non garantisce accettazione antivirus. Smart App Control/MOTW e le policy che bloccano script scaricati richiedono un collaudo distinto. Non disattivare protezioni per dichiarare una verifica riuscita.
