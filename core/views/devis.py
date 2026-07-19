
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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import Produit, DemandeDevis


@login_required
def demande_devis(request, produit_id=None):
    """Page de demande de devis"""
    produit = None
    if produit_id:
        produit = get_object_or_404(Produit, id=produit_id, en_vente=True)
    
    # 🔥 Récupérer tous les produits pour la liste déroulante
    tous_les_produits = Produit.objects.filter(en_vente=True).order_by('nom')
    
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        email = request.POST.get('email', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        message = request.POST.get('message', '').strip()
        produit_id_post = request.POST.get('produit_id')
        
        # Validation
        if not all([nom, email, telephone]):
            messages.error(request, "❌ Veuillez remplir tous les champs obligatoires.")
            return render(request, 'core/demande_devis.html', {
                'produit': produit,
                'produits': tous_les_produits,
                'nom': nom,
                'email': email,
                'telephone': telephone,
                'message': message
            })
        
        # Récupérer le produit si spécifié
        produit_obj = None
        if produit_id_post:
            try:
                produit_obj = Produit.objects.get(id=produit_id_post, en_vente=True)
            except Produit.DoesNotExist:
                pass
        
        # Créer la demande
        DemandeDevis.objects.create(
            nom=nom,
            email=email,
            telephone=telephone,
            produit=produit_obj,
            message=message
        )
        
        messages.success(
            request, 
            "✅ Votre demande de devis a été envoyée ! Nous vous contacterons dans les plus brefs délais."
        )
        return redirect('core:produits')
    
    context = {
        'produit': produit,
        'produits': tous_les_produits,  # ← Pour la liste déroulante
    }
    return render(request, 'core/demande_devis.html', context)


@login_required    
def mes_devis(request):
    """Voir l'historique des devis d'un client"""
    devis = DemandeDevis.objects.filter(email=request.user.email).order_by('-date_demande')
    
    context = {
        'devis': devis,
    }
    return render(request, 'core/mes_devis.html', context)
