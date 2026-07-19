from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re


def inscription(request):
    """Page d'inscription sécurisée"""
    if request.user.is_authenticated:
        return redirect('core:accueil')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # === VALIDATIONS ===
        erreurs = []
        
        # 1. Vérifier que tous les champs sont remplis
        if not username or not email or not password1 or not password2:
            erreurs.append("Tous les champs sont obligatoires.")
        
        # 2. Valider l'email
        if email:
            try:
                validate_email(email)
            except ValidationError:
                erreurs.append("L'adresse email n'est pas valide.")
        
        # 3. Vérifier les mots de passe
        if password1 and password2 and password1 != password2:
            erreurs.append("Les mots de passe ne correspondent pas.")
        
        if password1 and len(password1) < 8:
            erreurs.append("Le mot de passe doit contenir au moins 8 caractères.")
        
        # 4. Vérifier que l'username n'existe pas
        if username and User.objects.filter(username=username).exists():
            erreurs.append("Ce nom d'utilisateur est déjà pris.")
        
        # 5. Vérifier que l'email n'existe pas
        if email and User.objects.filter(email=email).exists():
            erreurs.append("Cet email est déjà utilisé.")
        
        # 6. Sécurité : mot de passe pas trop simple
        if password1 and len(password1) >= 8:
            if password1.lower() == username.lower():
                erreurs.append("Le mot de passe ne peut pas être identique au nom d'utilisateur.")
            if re.search(r'^[0-9]+$', password1):
                erreurs.append("Le mot de passe ne peut pas être uniquement numérique.")
        
        # Si erreurs, on affiche
        if erreurs:
            for erreur in erreurs:
                messages.error(request, erreur)
            return render(request, 'core/inscription.html', {
                'username': username,
                'email': email,
            })
        
        # === CRÉATION DU COMPTE ===
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            # Le signal va créer le panier automatiquement
            
            messages.success(request, f"🎉 Bienvenue {username} ! Votre compte a été créé avec succès.")
            login(request, user)
            return redirect('core:accueil')
            
        except Exception as e:
            messages.error(request, f"Une erreur est survenue : {str(e)}")
            return render(request, 'core/inscription.html', {
                'username': username,
                'email': email,
            })
    
    return render(request, 'core/inscription.html')


def connexion(request):
    """Page de connexion sécurisée"""
    if request.user.is_authenticated:
        return redirect('core:accueil')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, "Veuillez remplir tous les champs.")
            return render(request, 'core/connexion.html')
        
        # Authentification
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"🔑 Bienvenue {user.username} !")
            
            # Rediriger vers la page demandée ou l'accueil
            next_url = request.GET.get('next', 'core:accueil')
            return redirect(next_url)
        else:
            messages.error(request, "❌ Nom d'utilisateur ou mot de passe incorrect.")
    
    return render(request, 'core/connexion.html')


def deconnexion(request):
    """Déconnexion"""
    logout(request)
    messages.info(request, "👋 Vous avez été déconnecté avec succès.")
    return redirect('core:connexion')


@login_required
def accueil(request):
    """Page d'accueil"""
    return render(request, 'core/accueil.html')