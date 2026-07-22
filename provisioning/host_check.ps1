# host_check.ps1 — run on the student's OWN Windows machine at T-14.
# Right-click > Run with PowerShell (or:  powershell -ExecutionPolicy Bypass -File host_check.ps1)
# Read-only checks; answers: can this laptop run the lab VM?

$pass = $true
function OK($m)   { Write-Host "[ok] $m" -ForegroundColor Green }
function WARN($m) { Write-Host "[??] $m" -ForegroundColor Yellow }
function FAIL($m) { Write-Host "[!!] $m" -ForegroundColor Red; $script:pass = $false }

Write-Host "== Digital Twin Lab - host compatibility check =="
$arch = $env:PROCESSOR_ARCHITECTURE
Write-Host "System: Windows / $arch"

if ($arch -ne "AMD64") {
    FAIL "Windows-on-ARM detected - VirtualBox amd64 image will not run. Use the Codespaces fallback."
}

# --- virtualization firmware ---
try {
    $cpu = Get-CimInstance Win32_Processor
    if ($cpu.VirtualizationFirmwareEnabled) {
        OK "Hardware virtualization ENABLED in firmware"
    } else {
        $ci = Get-ComputerInfo -Property HyperVisorPresent -ErrorAction SilentlyContinue
        if ($ci.HyperVisorPresent) {
            WARN "Virtualization present but a hypervisor (Hyper-V) already owns it - see next check."
        } else {
            FAIL "Virtualization DISABLED in BIOS/UEFI. Reboot into firmware settings and enable 'Intel VT-x' / 'AMD-V' / 'SVM Mode'. On locked corporate laptops this may be impossible -> Codespaces fallback."
        }
    }
} catch { WARN "Could not query virtualization state: $_" }

# --- Hyper-V coexistence (the classic VirtualBox-on-Windows failure) ---
$hv = Get-CimInstance Win32_ComputerSystem
if ($hv.HypervisorPresent) {
    WARN ("Hyper-V / Virtual Machine Platform is active (WSL2, Docker Desktop, " +
          "Device Guard). Modern VirtualBox (7.x) CAN run alongside it but " +
          "noticeably slower. If the VM crawls or crashes: either accept " +
          "Codespaces, or (advanced, admin needed) disable 'Virtual Machine " +
          "Platform' + 'Windows Hypervisor Platform' in Windows Features and reboot.")
} else {
    OK "No competing hypervisor active - VirtualBox gets full speed"
}

# --- RAM ---
$ramGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
if     ($ramGB -ge 16) { OK "RAM: $ramGB GB - give the VM 8 GB" }
elseif ($ramGB -ge 12) { OK "RAM: $ramGB GB - give the VM 6 GB" }
elseif ($ramGB -ge 8)  { WARN "RAM: $ramGB GB - set the VM to 5 GB and close everything else. Workable, not comfortable." }
else                   { FAIL "RAM: $ramGB GB - too little to host the VM. Codespaces." }

# --- disk ---
$freeGB = [math]::Round((Get-PSDrive -Name ($env:SystemDrive.TrimEnd(':'))).Free / 1GB)
if ($freeGB -ge 30) { OK "Free disk: $freeGB GB" }
else                { FAIL "Free disk: $freeGB GB - need ~30 GB." }

Write-Host ""
if ($pass) {
    Write-Host "VERDICT: this machine can run the lab VM." -ForegroundColor Green
    Write-Host "Download: dtlab-amd64.ova (hypervisor: VirtualBox)"
    Write-Host "Next: import it, boot, and complete the T-7 smoke-test checkpoint."
} else {
    Write-Host "VERDICT: use the Codespaces fallback route (see handout) - or fix the [!!] items and re-run." -ForegroundColor Red
}
