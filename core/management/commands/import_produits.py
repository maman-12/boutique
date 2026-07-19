from django.core.management.base import BaseCommand
from core.models import Categorie, Produit

class Command(BaseCommand):
    help = 'Importe des produits de test'

    def handle(self, *args, **kwargs):
        # === CRÉER LES CATÉGORIES ===
        categories = [
            'Téléphones',
            'Ordinateurs',
            'Accessoires',
            'TV & Audio',
            'Électroménager',
        ]
        
        for cat in categories:
            Categorie.objects.get_or_create(nom=cat)
        
        self.stdout.write('✅ Catégories créées')
        
        # === CRÉER LES PRODUITS ===
        produits = [
            {
                'nom': 'iPhone 15 Pro',
                'description': 'Smartphone Apple avec écran 6.1" OLED, puce A17 Pro, appareil photo 48MP',
                'prix': 1250000,
                'stock': 10,
                'categorie': 'Téléphones'
            },
            {
                'nom': 'Samsung Galaxy S24 Ultra',
                'description': 'Smartphone Samsung avec écran 6.8" Dynamic AMOLED, S Pen intégré',
                'prix': 1100000,
                'stock': 15,
                'categorie': 'Téléphones'
            },
            {
                'nom': 'MacBook Air M2',
                'description': 'Ordinateur portable Apple 13" avec puce M2, 8GB RAM, 256GB SSD',
                'prix': 1500000,
                'stock': 8,
                'categorie': 'Ordinateurs'
            },
            {
                'nom': 'Dell XPS 13',
                'description': 'Ordinateur portable Dell 13" avec processeur Intel Core i7, 16GB RAM',
                'prix': 1350000,
                'stock': 6,
                'categorie': 'Ordinateurs'
            },
            {
                'nom': 'AirPods Pro 2',
                'description': 'Écouteurs sans fil Apple avec réduction de bruit active et spatial audio',
                'prix': 185000,
                'stock': 20,
                'categorie': 'Accessoires'
            },
            {
                'nom': 'Chargeur Samsung 25W',
                'description': 'Chargeur rapide USB-C 25W pour smartphones Samsung',
                'prix': 15000,
                'stock': 30,
                'categorie': 'Accessoires'
            },
            {
                'nom': 'TV Samsung 55" QLED',
                'description': 'Téléviseur 4K QLED 55 pouces avec Smart TV, HDR10+',
                'prix': 850000,
                'stock': 5,
                'categorie': 'TV & Audio'
            },
            {
                'nom': 'Enceinte JBL Flip 6',
                'description': 'Enceinte Bluetooth portable, étanche IP67, son puissant',
                'prix': 75000,
                'stock': 12,
                'categorie': 'TV & Audio'
            },
            {
                'nom': 'Réfrigérateur LG 400L',
                'description': 'Réfrigérateur double porte Inverter 400L, classe A+++',
                'prix': 950000,
                'stock': 3,
                'categorie': 'Électroménager'
            },
            {
                'nom': 'Machine à laver Samsung 7kg',
                'description': 'Lave-linge Samsung 7kg, technologie EcoBubble, classe A',
                'prix': 650000,
                'stock': 4,
                'categorie': 'Électroménager'
            },
        ]
        
        for prod in produits:
            categorie = Categorie.objects.get(nom=prod['categorie'])
            Produit.objects.get_or_create(
                nom=prod['nom'],
                defaults={
                    'description': prod['description'],
                    'prix': prod['prix'],
                    'stock': prod['stock'],
                    'categorie': categorie,
                    'en_vente': True,
                }
            )
        
        self.stdout.write(f'✅ {len(produits)} produits créés')
        self.stdout.write(self.style.SUCCESS('🎉 Import terminé !'))