from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib import messages
from core.models import Societe
from core.forms import InscriptionEntrepriseForm


def inscription_entreprise(request):
    """
    Vue pour inscrire une nouvelle entreprise
    L'admin crée un compte pour l'entreprise avec email et mot de passe
    """
    if request.method == 'POST':
        form = InscriptionEntrepriseForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Créer l'utilisateur
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Vérifier que l'email n'existe pas déjà
            if User.objects.filter(email=email).exists():
                messages.error(request, "❌ Cet email est déjà utilisé.")
                return render(request, 'core/inscription_entreprise.html', {'form': form})
            
            if User.objects.filter(username=username).exists():
                messages.error(request, "❌ Ce nom d'utilisateur est déjà pris.")
                return render(request, 'core/inscription_entreprise.html', {'form': form})
            
            # Créer l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=False,  # Pas un admin
                is_superuser=False
            )
            
            # 2. Créer la société liée à l'utilisateur
            societe = Societe.objects.create(
                nom=form.cleaned_data['nom'],
                email=email,
                telephone=form.cleaned_data['telephone'],
                adresse=form.cleaned_data['adresse'],
                ville=form.cleaned_data['ville'],
                user=user,
                logo=form.cleaned_data.get('logo'),
                commission_par_defaut=form.cleaned_data.get('commission_par_defaut', 15),
                actif=True
            )
            
            messages.success(
                request, 
                f"✅ Entreprise '{societe.nom}' créée avec succès ! "
                f"L'entreprise peut maintenant se connecter avec :\n"
                f"👤 {username}\n"
                f"🔑 {password}"
            )
            
            # Optionnel : connecter automatiquement l'admin (celui qui crée)
            # Mais on laisse l'entreprise se connecter elle-même
            return redirect('core:connexion_entreprise')
    else:
        form = InscriptionEntrepriseForm()
    
    return render(request, 'core/inscription_entreprise.html', {'form': form})


def connexion_entreprise(request):
    """
    Vue pour connecter une entreprise
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authentifier l'utilisateur
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Vérifier que l'utilisateur a bien une société
            try:
                societe = user.societe
                if societe.actif:
                    login(request, user)
                    messages.success(request, f"🔑 Bienvenue {societe.nom} !")
                    return redirect('core:dashboard_entreprise')
                else:
                    messages.error(request, "❌ Votre compte entreprise est désactivé. Contactez l'administrateur.")
            except Societe.DoesNotExist:
                messages.error(request, "❌ Ce compte n'est pas associé à une entreprise.")
        else:
            messages.error(request, "❌ Nom d'utilisateur ou mot de passe incorrect.")
    
    return render(request, 'core/connexion_entreprise.html')