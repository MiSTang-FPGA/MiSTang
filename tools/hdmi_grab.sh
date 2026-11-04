#!/usr/bin/env bash
# Grab one 720p frame from a UVC capture card on the board's HDMI (Windows/dshow). usage: hdmi_grab.sh out.png [device-name]
FF=${FFMPEG:-/e/tools/ffmpeg/ffmpeg-N-127617-g94cba3150c-win64-gpl/bin/ffmpeg.exe}
OUT=$(cygpath -w "$(realpath -m "$1")"); DEV=${2:-USB3.0 UHD}
"$FF" -hide_banner -loglevel error -y -f dshow -video_size ${SIZE:-1280x720} -i video="$DEV" -frames:v 30 -update 1 "$OUT"
