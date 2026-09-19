$ErrorActionPreference = 'Stop'
$taskRoot = [System.IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\')
if ((Split-Path $taskRoot -Leaf) -ne 'RuoYi-Vue3-FastAPI-miniapp-backend') {
  throw 'This starter may run only from the independent development copy.'
}

# Keep this launcher bound to the isolated activity database.
$taskDatabase = 'nsh_activity_dev_20260914'
if ($taskDatabase -notmatch '^nsh_activity_dev_[0-9]{8}$' -or $taskDatabase -eq 'ruoyi') {
  throw "Unsafe development database name: $taskDatabase"
}

$taskBackendDir = Join-Path $taskRoot 'ruoyi-fastapi-backend'
$taskFrontendDir = Join-Path $taskRoot 'ruoyi-fastapi-frontend'
$taskPython = Join-Path $taskBackendDir '.venv\Scripts\python.exe'
$taskVite = Join-Path $taskFrontendDir 'node_modules\vite\bin\vite.js'
$taskLogDir = Join-Path $taskRoot 'logs\activity-dev'
$taskStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$taskBackendOut = Join-Path $taskLogDir "backend-$taskStamp.out.log"
$taskBackendErr = Join-Path $taskLogDir "backend-$taskStamp.err.log"
$taskFrontendOut = Join-Path $taskLogDir "frontend-$taskStamp.out.log"
$taskFrontendErr = Join-Path $taskLogDir "frontend-$taskStamp.err.log"

foreach ($taskRequired in @($taskPython, $taskVite)) {
  if (-not (Test-Path -LiteralPath $taskRequired -PathType Leaf)) {
    throw "Required runtime file is missing: $taskRequired"
  }
}
if (-not (Get-Command node.exe -ErrorAction SilentlyContinue)) {
  throw 'node.exe was not found. Install Node.js before starting the project.'
}
New-Item -ItemType Directory -Force -Path $taskLogDir | Out-Null

function Get-TaskListenerPid([int]$Port) {
  $taskIds = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique)
  if ($taskIds.Count -gt 1) { throw "Port $Port has multiple listeners." }
  if ($taskIds.Count -eq 1) { return [int]$taskIds[0] }
  return 0
}

foreach ($taskPort in @(5173, 9101)) {
  $taskExistingPid = Get-TaskListenerPid $taskPort
  if ($taskExistingPid) {
    throw "Port $taskPort is already in use by PID $taskExistingPid. Close the previous project window first."
  }
}

if (-not ('ProjectJob' -as [type])) {
  Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

public static class ProjectJob
{
    public const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000;

    [StructLayout(LayoutKind.Sequential)]
    public struct JOBOBJECT_BASIC_LIMIT_INFORMATION
    {
        public long PerProcessUserTimeLimit;
        public long PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass;
        public uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct IO_COUNTERS
    {
        public ulong ReadOperationCount;
        public ulong WriteOperationCount;
        public ulong OtherOperationCount;
        public ulong ReadTransferCount;
        public ulong WriteTransferCount;
        public ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION
    {
        public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;
        public IO_COUNTERS IoInfo;
        public UIntPtr ProcessMemoryLimit;
        public UIntPtr JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed;
        public UIntPtr PeakJobMemoryUsed;
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr CreateJobObject(IntPtr securityAttributes, string name);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool SetInformationJobObject(
        IntPtr job,
        int informationClass,
        IntPtr information,
        uint informationLength);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool CloseHandle(IntPtr handle);

    public static IntPtr CreateKillOnCloseJob()
    {
        IntPtr job = CreateJobObject(IntPtr.Zero, null);
        if (job == IntPtr.Zero)
            throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateJobObject failed");

        JOBOBJECT_EXTENDED_LIMIT_INFORMATION info = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION();
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        int length = Marshal.SizeOf(typeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION));
        IntPtr pointer = Marshal.AllocHGlobal(length);
        try
        {
            Marshal.StructureToPtr(info, pointer, false);
            if (!SetInformationJobObject(job, 9, pointer, (uint)length))
            {
                int error = Marshal.GetLastWin32Error();
                CloseHandle(job);
                throw new Win32Exception(error, "SetInformationJobObject failed");
            }
        }
        finally
        {
            Marshal.FreeHGlobal(pointer);
        }
        return job;
    }
}
'@
}

function Add-TaskProcessToJob([IntPtr]$Job, [System.Diagnostics.Process]$Process, [string]$Name) {
  if (-not [ProjectJob]::AssignProcessToJobObject($Job, $Process.Handle)) {
    $taskError = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
    Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
    throw "Could not attach $Name to the project supervisor. Win32 error: $taskError"
  }
}

function Wait-TaskHealth([string]$Name, [string]$Url, [int]$Port, [string]$ErrorLog, [System.Diagnostics.Process]$Process) {
  for ($taskTry = 0; $taskTry -lt 60; $taskTry++) {
    if ($Process.HasExited) {
      if (Test-Path -LiteralPath $ErrorLog) { Get-Content -LiteralPath $ErrorLog -Tail 30 }
      throw "$Name exited before it became ready. Exit code: $($Process.ExitCode)"
    }
    try {
      $taskResponse = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
      if ($taskResponse.StatusCode -eq 200) {
        Write-Output "$Name is ready: $Url"
        return
      }
    } catch {}
    Start-Sleep -Milliseconds 500
  }
  if (Test-Path -LiteralPath $ErrorLog) { Get-Content -LiteralPath $ErrorLog -Tail 30 }
  throw "$Name health check timed out on port ${Port}: $Url"
}

function Wait-TaskServices([System.Diagnostics.Process]$Backend, [System.Diagnostics.Process]$Frontend) {
  Write-Output ''
  Write-Output 'PROJECT IS RUNNING'
  Write-Output 'Keep this CMD window open. Closing it stops the frontend and backend.'
  Write-Output 'Frontend: http://127.0.0.1:5173/personal/battle-information/mine'
  Write-Output 'Backend docs: http://127.0.0.1:9101/docs'
  Write-Output 'Mini-program API: http://127.0.0.1:9101/api/v1'
  Write-Output "Logs: $taskLogDir"
  Write-Output ''
  Write-Output 'Do not close this window while using the project.'

  while ($true) {
    if ($Backend.HasExited) {
      if (Test-Path -LiteralPath $taskBackendErr) { Get-Content -LiteralPath $taskBackendErr -Tail 30 }
      throw "Backend stopped unexpectedly. Exit code: $($Backend.ExitCode)"
    }
    if ($Frontend.HasExited) {
      if (Test-Path -LiteralPath $taskFrontendErr) { Get-Content -LiteralPath $taskFrontendErr -Tail 30 }
      throw "Frontend stopped unexpectedly. Exit code: $($Frontend.ExitCode)"
    }
    Start-Sleep -Seconds 1
  }
}

$taskJob = [IntPtr]::Zero
$taskBackendProcess = $null
$taskFrontendProcess = $null
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:APP_ENV = 'dev'
$env:APP_HOST = '127.0.0.1'
$env:APP_PORT = '9101'
$env:DB_DATABASE = $taskDatabase
$env:NSH_ACTIVITIES_ENABLED = 'true'
$env:LOG_MASK_ENABLED = 'true'

try {
  $taskJob = [ProjectJob]::CreateKillOnCloseJob()

  Write-Output "Starting backend with database $taskDatabase..."
  $taskBackendProcess = Start-Process -FilePath $taskPython `
    -ArgumentList 'tools/local_activity_dev.py serve' -WorkingDirectory $taskBackendDir `
    -WindowStyle Hidden -RedirectStandardOutput $taskBackendOut `
    -RedirectStandardError $taskBackendErr -PassThru
  Add-TaskProcessToJob $taskJob $taskBackendProcess 'backend'

  Write-Output 'Starting frontend...'
  $taskFrontendProcess = Start-Process -FilePath 'node.exe' `
    -ArgumentList 'node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort' `
    -WorkingDirectory $taskFrontendDir -WindowStyle Hidden `
    -RedirectStandardOutput $taskFrontendOut -RedirectStandardError $taskFrontendErr -PassThru
  Add-TaskProcessToJob $taskJob $taskFrontendProcess 'frontend'

  Wait-TaskHealth 'Backend' 'http://127.0.0.1:9101/api/v1/auth/config' 9101 $taskBackendErr $taskBackendProcess
  Wait-TaskHealth 'Frontend' 'http://127.0.0.1:5173/login' 5173 $taskFrontendErr $taskFrontendProcess
  Wait-TaskServices $taskBackendProcess $taskFrontendProcess
}
finally {
  if ($taskJob -ne [IntPtr]::Zero) {
    [ProjectJob]::CloseHandle($taskJob) | Out-Null
  }
  for ($taskTry = 0; $taskTry -lt 30; $taskTry++) {
    if (-not (Get-TaskListenerPid 5173) -and -not (Get-TaskListenerPid 9101)) { break }
    Start-Sleep -Milliseconds 200
  }
  Write-Output 'Project supervisor stopped. Frontend and backend were closed.'
}
