#!/bin/bash
# 1. Maak de juiste submap aan
mkdir -p kidslock-manager

echo "Start herstructurering..."

# 2. Verplaats bestanden als ze in de root staan
for file in config.yaml Dockerfile main.py requirements.txt run.sh README.md; do
    if [ -f "$file" ]; then
        mv "$file" kidslock-manager/
        echo "Verplaatst: $file"
    fi
done

# 3. Verplaats templates
if [ -d "templates" ]; then
    mv templates kidslock-manager/
    echo "Verplaatst: templates map"
fi

# 4. Verwijder de oude/foutieve 'kidslock' map als die nog bestaat
rm -rf kidslock

echo "--- CONTROLE ---"
echo "Root map (moet repository.yaml bevatten):"
ls -1
echo "---"
echo "Submap kidslock-manager (moet config.yaml, Dockerfile, etc. bevatten):"
ls -1 kidslock-manager/
echo "---"
echo "Als dit klopt: git add ., git commit en git push uitvoeren!"