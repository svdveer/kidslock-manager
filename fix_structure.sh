#!/bin/bash
# 1. Maak de juiste submap aan
mkdir -p kidslock-manager

echo "Start herstructurering v1.1.3..."

# 2. Verplaats bestanden (Toegevoegd: CHANGELOG.md)
for file in config.yaml Dockerfile main.py requirements.txt run.sh README.md CHANGELOG.md; do
    if [ -f "$file" ]; then
        mv -f "$file" kidslock-manager/
        echo "Verplaatst: $file naar kidslock-manager/"
    fi
done

# 3. Verplaats templates
if [ -d "templates" ]; then
    # -T zorgt ervoor dat de inhoud netjes wordt samengevoegd/overschreven
    cp -rf templates kidslock-manager/
    rm -rf templates
    echo "Verplaatst: templates map naar kidslock-manager/"
fi

# 4. Verwijder de oude/foutieve 'kidslock' map als die nog bestaat
rm -rf kidslock

# 5. Opschonen root (voor de zekerheid)
rm -f config.yaml Dockerfile main.py requirements.txt run.sh CHANGELOG.md

echo "--- CONTROLE ---"
echo "Root map (moet repository.yaml en kidslock-manager/ bevatten):"
ls -F
echo "---"
echo "Submap kidslock-manager (moet config.yaml, main.py, CHANGELOG.md, etc. bevatten):"
ls -1 kidslock-manager/
echo "---"
echo "Check gelukt? Voer dan uit: git add . && git commit -m 'Structure fix v1.1.3' && git push"