#!/usr/bin/with-contenv bashio

echo "--- KidsLock Manager v1.4.5 Starten ---"

# Gebruik 'exec' om Python als hoofdproces (PID 1) te laten draaien
exec python3 /app/main.py