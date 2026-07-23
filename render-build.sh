#!/bin/bash
# render-build.sh

echo "🐍 Installation des dépendances système..."
apt-get update
apt-get install -y \
    python3-dev \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    zlib1g-dev \
    gcc \
    g++

echo "📦 Installation des paquets Python..."
pip install -r requirements.txt

echo "📊 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "✅ Build terminé avec succès !"
