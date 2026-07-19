from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.shortcuts import render,redirect,get_list_or_404,get_object_or_404
from django.contrib import messages
import secrets
from datetime import timedelta
from core.models import TokenReinitialisation
from django.contrib.auth.models import User
import re

# ============================================
# RÉINITIALISATION DU MOT DE PASSE
# ============================================

def mot_de_passe_oublie(request):
    """Page pour demander la réinitialisation du mot de passe"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, "❌ Veuillez entrer votre adresse email.")
            return render(request, 'core/mot_de_passe_oublie.html')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "❌ Aucun compte trouvé avec cet email.")
            return render(request, 'core/mot_de_passe_oublie.html')
        
        # Générer un token unique
        token = secrets.token_urlsafe(32)
        
        # Supprimer les anciens tokens non utilisés
        TokenReinitialisation.objects.filter(
            user=user,
            utilise=False,
            date_expiration__lt=timezone.now()
        ).delete()
        
        # Créer le nouveau token
        token_obj = TokenReinitialisation.objects.create(
            user=user,
            token=token,
            date_expiration=timezone.now() + timedelta(hours=24)
        )
        
        # Construire le lien de réinitialisation
        lien_reinitialisation = request.build_absolute_uri(
            reverse('core:reinitialiser_mot_de_passe', args=[token])
        )
        
        # Envoyer l'email
        sujet = "Réinitialisation de votre mot de passe - Ma Boutique"
        message = f"""
Bonjour {user.username},

Vous avez demandé la réinitialisation de votre mot de passe sur Ma Boutique.

Cliquez sur le lien ci-dessous pour créer un nouveau mot de passe :
{lien_reinitialisation}

Ce lien est valable 24 heures.

Si vous n'êtes pas à l'origine de cette demande, ignorez simplement cet email.

Merci,
L'équipe Ma Boutique
"""
        
        try:
            send_mail(
                sujet,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            messages.success(
                request, 
                f"✅ Un email a été envoyé à {email} avec les instructions pour réinitialiser votre mot de passe."
            )
        except Exception as e:
            messages.error(
                request, 
                f"❌ Une erreur est survenue lors de l'envoi de l'email. Veuillez réessayer."
            )
            print(f"Erreur d'envoi d'email : {e}")
        
        return redirect('core:connexion')
    
    return render(request, 'core/mot_de_passe_oublie.html')


def reinitialiser_mot_de_passe(request, token):
    """Page pour réinitialiser le mot de passe avec le token"""
    
    try:
        token_obj = TokenReinitialisation.objects.get(token=token)
    except TokenReinitialisation.DoesNotExist:
        messages.error(request, "❌ Ce lien est invalide ou a déjà été utilisé.")
        return redirect('core:connexion')
    
    # Vérifier si le token est valide
    if not token_obj.est_valide():
        messages.error(request, "❌ Ce lien a expiré. Veuillez faire une nouvelle demande.")
        return redirect('core:mot_de_passe_oublie')
    
    user = token_obj.user
    
    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # === VALIDATIONS ===
        erreurs = []
        
        if not password1 or not password2:
            erreurs.append("Tous les champs sont obligatoires.")
        
        if password1 != password2:
            erreurs.append("Les mots de passe ne correspondent pas.")
        
        if len(password1) < 8:
            erreurs.append("Le mot de passe doit contenir au moins 8 caractères.")
        
        if password1.lower() == user.username.lower():
            erreurs.append("Le mot de passe ne peut pas être identique au nom d'utilisateur.")
        
        if re.search(r'^[0-9]+$', password1):
            erreurs.append("Le mot de passe ne peut pas être uniquement numérique.")
        
        if erreurs:
            for erreur in erreurs:
                messages.error(request, erreur)
            return render(request, 'core/reinitialiser_mot_de_passe.html', {'token': token})
        
        # Changer le mot de passe
        user.set_password(password1)
        user.save()
        
        # Marquer le token comme utilisé
        token_obj.utilise = True
        token_obj.save()
        
        messages.success(
            request, 
            "✅ Votre mot de passe a été réinitialisé avec succès ! Vous pouvez maintenant vous connecter."
        )
        return redirect('core:connexion')
    
    return render(request, 'core/reinitialiser_mot_de_passe.html', {'token': token})