from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Produit, Panier
import uuid


# === SIGNAL POUR LE QR CODE ===
@receiver(pre_save, sender=Produit)
def generer_qr_code_produit(sender, instance, **kwargs):
    """Génère automatiquement le QR code lors de la création d'un produit"""
    
    # Si le produit est nouveau (pas d'ID) ou si le QR code est vide
    if not instance.id or not instance.qr_code_image:
        # Générer la référence unique
        if not instance.reference_unique:
            instance.generer_reference_unique()
        
        # Générer le QR code
        instance.generer_qr_code()


# === SIGNAL POUR LE PANIER ===
@receiver(post_save, sender=User)
def creer_panier(sender, instance, created, **kwargs):
    """Crée un panier automatiquement quand un utilisateur s'inscrit"""
    if created:
        Panier.objects.create(utilisateur=instance)