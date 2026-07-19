
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
from core.models import*

@login_required
def stats_admin(request):
    """Tableau de bord des statistiques pour l'administrateur"""
    if not request.user.is_staff:
        messages.error(request, "⛔ Accès réservé à l'administration.")
        return redirect('core:accueil')
    
    from django.db.models import Count, Sum, Q
    from django.utils import timezone
    from datetime import timedelta
    
    # Statistiques générales
    total_produits = Produit.objects.count()
    total_commandes = Commande.objects.count()
    total_clients = User.objects.count()
    total_entreprises = Societe.objects.count()
    total_ventes = Commande.objects.aggregate(Sum('total'))['total__sum'] or 0
    total_demandes_devis = DemandeDevis.objects.count()
    
    # Commandes par statut
    commandes_par_statut = Commande.objects.values('statut').annotate(count=Count('id'))
    
    # Commandes du mois
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    commandes_mois = Commande.objects.filter(date_commande__gte=debut_mois)
    total_ventes_mois = commandes_mois.aggregate(Sum('total'))['total__sum'] or 0
    nb_commandes_mois = commandes_mois.count()
    
    # Dernières commandes
    dernieres_commandes = Commande.objects.all().order_by('-date_commande')[:10]
    
    # Meilleurs produits
    meilleurs_produits = LigneCommande.objects.values('produit__nom').annotate(
        total_vendu=Sum('quantite')
    ).order_by('-total_vendu')[:10]
    
    # Demandes de devis en attente
    devis_en_attente = DemandeDevis.objects.filter(traite=False).count()
    
    context = {
        'total_produits': total_produits,
        'total_commandes': total_commandes,
        'total_clients': total_clients,
        'total_entreprises': total_entreprises,
        'total_ventes': total_ventes,
        'total_demandes_devis': total_demandes_devis,
        'commandes_par_statut': commandes_par_statut,
        'total_ventes_mois': total_ventes_mois,
        'nb_commandes_mois': nb_commandes_mois,
        'dernieres_commandes': dernieres_commandes,
        'meilleurs_produits': meilleurs_produits,
        'devis_en_attente': devis_en_attente,
    }
                  
    return render(request, 'core/stats_admin.html', context)