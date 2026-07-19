from django.contrib.auth.decorators import user_passes_test
from core.forms import ProduitForm
from core.models import Societe, Produit, Categorie
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
from core.models import *

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from django.http import JsonResponse

# ============================================
# VUES POUR LES ENTREPRISES
# ============================================

def est_entreprise(user):
    """Vérifie si l'utilisateur est une entreprise"""
    return hasattr(user, 'societe') and user.societe.actif


@login_required
@user_passes_test(est_entreprise)
def dashboard_entreprise(request):
    """Dashboard de l'entreprise"""
    societe = request.user.societe
    produits = societe.produits.all()
    
    # Statistiques
    total_ventes = societe.total_ventes
    total_commissions = societe.total_commissions
    total_reversement = societe.total_reversement
    nb_produits = produits.count()
    
    # Dernières commandes
    from core.models import LigneCommande
    dernieres_ventes = LigneCommande.objects.filter(
        produit__societe=societe
    ).order_by('-commande__date_commande')[:10]
    
    context = {
        'societe': societe,
        'produits': produits,
        'total_ventes': total_ventes,
        'total_commissions': total_commissions,
        'total_reversement': total_reversement,
        'nb_produits': nb_produits,
        'dernieres_ventes': dernieres_ventes,
    }
    return render(request, 'core/dashboard_entreprise.html', context)


@login_required
@user_passes_test(est_entreprise)
def ajouter_produit(request):
    """Ajouter un produit par l'entreprise"""
    societe = request.user.societe
    
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        if form.is_valid():
            produit = form.save(commit=False)
            produit.societe = societe
            produit.calculer_commission()
            produit.save()
            messages.success(request, f"✅ Produit '{produit.nom}' ajouté avec succès !")
            return redirect('core:liste_produits_entreprise')
    else:
        form = ProduitForm()
    
    return render(request, 'core/ajouter_produit.html', {'form': form})


@login_required
@user_passes_test(est_entreprise)
def modifier_produit(request, produit_id):
    """Modifier un produit par l'entreprise"""
    societe = request.user.societe
    produit = get_object_or_404(Produit, id=produit_id, societe=societe)
    
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, instance=produit)
        if form.is_valid():
            produit = form.save(commit=False)
            produit.calculer_commission()
            produit.save()
            messages.success(request, f"✅ Produit '{produit.nom}' modifié avec succès !")
            return redirect('core:liste_produits_entreprise')
    else:
        form = ProduitForm(instance=produit)
    
    return render(request, 'core/modifier_produit.html', {'form': form, 'produit': produit})


@login_required
@user_passes_test(est_entreprise)
def liste_produits_entreprise(request):
    """Liste des produits de l'entreprise"""
    societe = request.user.societe
    produits = societe.produits.all()
    
    context = {
        'produits': produits,
        'societe': societe,
    }
    return render(request, 'core/produits_entreprise.html', context)


@login_required
@user_passes_test(est_entreprise)
def supprimer_produit(request, produit_id):
    """Supprimer un produit"""
    societe = request.user.societe
    produit = get_object_or_404(Produit, id=produit_id, societe=societe)
    
    if request.method == 'POST':
        nom = produit.nom
        produit.delete()
        messages.success(request, f"🗑️ Produit '{nom}' supprimé avec succès !")
        return redirect('core:liste_produits_entreprise')
    
    return render(request, 'core/supprimer_produit.html', {'produit': produit})