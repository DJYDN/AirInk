$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
$configDir = Join-Path $projectRoot "data/dev/config"
$configPath = Join-Path $configDir "config.json"

New-Item -ItemType Directory -Force -Path $configDir | Out-Null

$config = @{
    camera = @{
        index = 0
        width = 1280
        height = 720
        fps = 30
        mirror = $true
    }
    canvas = @{
        width = 1280
        height = 720
        background_color = "#FFFFFF"
    }
    pen = @{
        color = "#000000"
        width = 4
        opacity = 1.0
    }
    tracking = @{
        min_detection_confidence = 0.70
        min_tracking_confidence = 0.75
        landmark_smoothing = 0.35
        pinch_down_threshold = 0.28
        pinch_up_threshold = 0.34
        stable_frames = 3
        lost_frame_limit = 18
        gesture_stable_frames = 3
        fist_ratio_threshold = 0.58
        extended_ratio_threshold = 0.95
        session_idle_timeout_ms = 1500
    }
    filter = @{
        type = "deadzone"
        strength = 0.75
        deadzone = 2.0
        start_threshold = 0.0
        max_jump_distance = 320.0
    }
}

$config | ConvertTo-Json -Depth 8 | Set-Content -Path $configPath -Encoding UTF8
Write-Host "Stable AirInk config written to $configPath"
