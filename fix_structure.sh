#!/bin/bash
# 1. Maak de juiste submap aan
mkdir -p kidslock-manager

# 2. Verplaats alle add-on bestanden van root naar de submap
# (We gebruiken 2>/dev/null om foutmeldingen te onderdrukken als ze al verplaatst zijn)
mv config.yaml Dockerfile main.py requirements.txt run.sh README.md kidslock-manager/ 2>/dev/null

# 3. Verplaats de templates map
if [ -d "templates" ]; then
    mv templates kidslock-manager/
fi

# 4. Verwijder de oude/foutieve 'kidslock' map als die nog bestaat
rm -rf kidslock

echo "Structuur hersteld. Commit en push deze wijzigingen naar GitHub."