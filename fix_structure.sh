#!/bin/bash
# Maak de submap aan
mkdir -p kidslock-manager

# Verplaats de add-on bestanden naar de submap
mv config.yaml Dockerfile main.py requirements.txt run.sh README.md kidslock-manager/

# Verplaats de templates map als deze bestaat (voor de webinterface)
if [ -d "templates" ]; then
    mv templates kidslock-manager/
fi

echo "Structuur hersteld. Commit en push deze wijzigingen naar GitHub."