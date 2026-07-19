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

@login_required
def panier_count(request):
    """Retourne le nombre d'articles dans le panier (AJAX)"""
    panier, created = Panier.objects.get_or_create(utilisateur=request.user)
    return JsonResponse({'count': panier.get_nb_articles()})




# ============================================
# ACCUEIL - AFFICHE 5 PRODUITS
# ============================================
                                      

from django.utils import timezone
   
def accueil(request):
    """Page d'accueil avec 5 derniers produits"""
    produits_recents = Produit.objects.filter(en_vente=True, stock__gt=0).order_by('-date_ajout')[:5]
    total_produits = Produit.objects.filter(en_vente=True, stock__gt=0).count()
    categories = Categorie.objects.all()[:6]  # 6 catégories max
    
    context = {
        'produits_recents': produits_recents,
        'total_produits': total_produits,
        'categories': categories,
        'today': timezone.now().date(),  # ← Pour le badge "Nouveau"
        'user': request.user,
    }
    return render(request, 'core/accueil.html', context)

# ... (le reste de tes vues existantes)


# ============================================
# PRODUITS
# ============================================

from django.utils import timezone

def liste_produits(request):
    """Affiche tous les produits disponibles"""
    produits = Produit.objects.filter(en_vente=True, stock__gt=0)
    categories = Categorie.objects.all()
    
    # Filtre par catégorie
    categorie_id = request.GET.get('categorie')
    if categorie_id:
        produits = produits.filter(categorie_id=categorie_id)
    
    # Recherche
    recherche = request.GET.get('recherche')
    if recherche:
        produits = produits.filter(nom__icontains=recherche)
    
    context = {
        'produits': produits,
        'categories': categories,
        'categorie_active': int(categorie_id) if categorie_id else None,
        'recherche': recherche,
        'nb_produits': produits.count(),
        'today': timezone.now().date(),  # ← Pour le badge "Nouveau"
    }
    return render(request, 'core/produits.html', context)


def detail_produit(request, produit_id):
    """Affiche le détail d'un produit"""
    produit = get_object_or_404(Produit, id=produit_id, en_vente=True)
    
    # Produits similaires (même catégorie)
    similaires = Produit.objects.filter(
        categorie=produit.categorie,
        en_vente=True
    ).exclude(id=produit.id)[:4]
    
    context = {
        'produit': produit,
        'similaires': similaires,
    }
    return render(request, 'core/detail_produit.html', context)


# ============================================
# PANIER
# ============================================

@login_required
def panier(request):
    """Affiche le panier de l'utilisateur"""
    panier, created = Panier.objects.get_or_create(utilisateur=request.user)
    articles = panier.articles.select_related('produit').all()
    
    total = panier.get_total()
    nb_articles = panier.get_nb_articles()
    
    context = {
        'articles': articles,
        'total': total,
        'nb_articles': nb_articles,
    }
    return render(request, 'core/panier.html', context)


@login_required
def ajouter_panier(request, produit_id):
    """Ajoute un produit au panier"""
    produit = get_object_or_404(Produit, id=produit_id, en_vente=True)
    quantite = int(request.POST.get('quantite', 1))
    
    # Vérifier le stock
    if produit.stock < quantite:
        messages.error(request, f"❌ Stock insuffisant pour {produit.nom}")
        return redirect('core:detail_produit', produit_id=produit.id)
    
    # Récupérer le panier
    panier, created = Panier.objects.get_or_create(utilisateur=request.user)
    
    # Ajouter ou mettre à jour
    article, created = ArticlePanier.objects.get_or_create(
        panier=panier,
        produit=produit,
        defaults={
            'quantite': quantite,
            'prix_unitaire': produit.prix
        }
    )
    
    if not created:
        article.quantite += quantite
        article.save()    
        
    messages.success(request, f"✅ {produit.nom} ajouté au panier !")
    return redirect('core:panier')
     
      
@login_required
def supprimer_article_panier(request, article_id):
    """Supprime un article du panier"""
    article = get_object_or_404(ArticlePanier, id=article_id, panier__utilisateur=request.user)
    produit_nom = article.produit.nom
    article.delete()
    messages.success(request, f"🗑️ {produit_nom} retiré du panier")
    return redirect('core:panier')


@login_required
def modifier_quantite_panier(request, article_id):
    """Modifie la quantité d'un article"""
    article = get_object_or_404(ArticlePanier, id=article_id, panier__utilisateur=request.user)
    
    if request.method == 'POST':
        quantite = int(request.POST.get('quantite', 1))
        if quantite > 0 and quantite <= article.produit.stock:
            article.quantite = quantite
            article.save()
            messages.success(request, f"✅ Quantité mise à jour")
        else:
            messages.error(request, f"❌ Quantité invalide (stock max: {article.produit.stock})")
    
    return redirect('core:panier')


@login_required
def vider_panier(request):
    """Vide complètement le panier"""
    panier = Panier.objects.get(utilisateur=request.user)
    nb_articles = panier.articles.count()
    panier.articles.all().delete()
    messages.info(request, f"🗑️ {nb_articles} article(s) retiré(s) du panier")
    return redirect('core:panier')


# ============================================
# COMMANDES
# ============================================

@login_required
def passer_commande(request):
    """Passe la commande"""
    panier = Panier.objects.get(utilisateur=request.user)
    articles = panier.articles.select_related('produit').all()
    
    if not articles:
        messages.warning(request, "⚠️ Votre panier est vide")
        return redirect('core:panier')
    
    if request.method == 'POST':
        # Récupérer les données
        nom_complet = request.POST.get('nom_complet', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        adresse = request.POST.get('adresse', '').strip()
        ville = request.POST.get('ville', '').strip()
        mode_paiement = request.POST.get('mode_paiement', '')
        
        # Valider   
        if not all([nom_complet, telephone, adresse, ville, mode_paiement]):
            messages.error(request, "❌ Tous les champs sont obligatoires")
            return redirect('core:commande')
        
        # Créer la commande   
        total = panier.get_total()
        
        commande = Commande.objects.create(
            client=request.user,
            nom_complet=nom_complet,
            telephone=telephone,
            adresse_livraison=adresse,
            ville=ville,
            mode_paiement=mode_paiement,
            total=total,
        )
        
        # Créer les lignes de commande
        for article in articles:
            LigneCommande.objects.create(
                commande=commande,
                produit=article.produit,
                quantite=article.quantite,
                prix_unitaire=article.prix_unitaire,
            )
            
            # Réduire le stock
            article.produit.stock -= article.quantite
            article.produit.save()
        
        # Vider le panier
        panier.articles.all().delete()
        
        messages.success(request, f"🎉 Commande #{commande.id} validée !")
        return redirect('core:confirmation', commande_id=commande.id)
    
    context = {
        'articles': articles,
        'total': panier.get_total(),
        'nb_articles': panier.get_nb_articles(),
    }
    return render(request, 'core/commande.html', context)


@login_required
def confirmation_commande(request, commande_id):
    """Page de confirmation de commande"""
    commande = get_object_or_404(Commande, id=commande_id, client=request.user)
    lignes = commande.lignes.select_related('produit').all()
    
    context = {
        'commande': commande,
        'lignes': lignes,
    }
    return render(request, 'core/confirmation.html', context)


@login_required
def historique_commandes(request):
    """Historique des commandes du client"""
    commandes = Commande.objects.filter(client=request.user).order_by('-date_commande')
    
    context = {
        'commandes': commandes,
    }
    return render(request, 'core/historique.html', context)





@login_required
def ajouter_favori(request, produit_id):
    """Ajoute ou retire un produit des favoris"""
    produit = get_object_or_404(Produit, id=produit_id, en_vente=True)
    favori, created = Favori.objects.get_or_create(
        utilisateur=request.user,
        produit=produit
    )
    
    if not created:
        favori.delete()
        messages.success(request, f"❌ {produit.nom} retiré des favoris")
    else:
        messages.success(request, f"❤️ {produit.nom} ajouté aux favoris")
    
    # Redirection vers la page précédente
    next_url = request.META.get('HTTP_REFERER', 'core:produits')
    return redirect(next_url)

@login_required
def mes_favoris(request):
    """Affiche les favoris de l'utilisateur"""
    favoris = Favori.objects.filter(utilisateur=request.user).select_related('produit')
    
    context = {
        'favoris': favoris,
    }
    return render(request, 'core/favoris.html', context)


@login_required
def chat(request):
    return render(request, 'core/chat.html')


@login_required
def noter_produit(request, produit_id):
    """Ajoute ou modifie une notation"""
    produit = get_object_or_404(Produit, id=produit_id, en_vente=True)
    
    if request.method == 'POST':
        note = request.POST.get('note')
        commentaire = request.POST.get('commentaire', '')
        
        if note:
            notation, created = Notation.objects.get_or_create(
                produit=produit,
                utilisateur=request.user,
                defaults={'note': note, 'commentaire': commentaire}
            )
            
            if not created:
                notation.note = note
                notation.commentaire = commentaire
                notation.save()
            
            messages.success(request, f"✅ Merci pour votre notation !")
        else:
            messages.error(request, "❌ Veuillez sélectionner une note.")
    
    return redirect('core:detail_produit', produit_id=produit.id)


def profile(request):
    return render(request,"core/profile.html")




    from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from core.models import MessageChat
from django.contrib.auth.models import User

@login_required
def chat_interface(request):
    """Interface de chat"""
    context = {
        'is_support': request.user.is_staff,
        'user_id': request.user.id,
    }
    return render(request, 'core/chat_interface.html', context)


@login_required
def chat_contacts(request):
    """Retourne la liste des contacts pour le chat (AJAX)"""
    if request.user.is_staff:
        clients = User.objects.filter(
            messages_envoyes__isnull=False
        ).exclude(is_staff=True).distinct()
        
        contacts = []
        for client in clients:
            last_msg = client.messages_envoyes.last()
            unread = client.messages_envoyes.filter(lu=False).count()
            contacts.append({
                'username': client.username,
                'email': client.email,
                'last_message': last_msg.contenu[:50] if last_msg else '',
                'unread': unread,
                'time': last_msg.date_envoi.strftime('%H:%M') if last_msg else '',
            })
    else:
        try:
            admin = User.objects.get(username='admin')
            last_msg = MessageChat.objects.filter(
                models.Q(expediteur=admin, destinataire=request.user) |
                models.Q(expediteur=request.user, destinataire=admin)
            ).last()
            
            contacts = [{
                'username': 'admin',
                'email': 'support@boutique.com',
                'last_message': last_msg.contenu[:50] if last_msg else 'Bonjour, comment puis-je vous aider ?',
                'unread': 0,
                'time': last_msg.date_envoi.strftime('%H:%M') if last_msg else '',
            }]
        except User.DoesNotExist:
            contacts = [{
                'username': 'admin',
                'email': 'support@boutique.com',
                'last_message': 'Support disponible',
                'unread': 0,
                'time': '',
            }]
    
    return JsonResponse({'contacts': contacts})

