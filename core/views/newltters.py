from django.core.mail import send_mail
from django.conf import settings
from core.models import AbonneNewsletter, EmailNewsletter
from django.shortcuts import redirect,render
from django.contrib import messages

def newsletter_abonnement(request):
    """Page d'abonnement à la newsletter"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        nom = request.POST.get('nom', '').strip()
        
        if not email:
            messages.error(request, "❌ Veuillez entrer votre email.")
            return redirect('core:newsletter_abonnement')
        
        # Vérifier si déjà abonné
        if AbonneNewsletter.objects.filter(email=email).exists():
            messages.warning(request, "⚠️ Cet email est déjà abonné à notre newsletter.")
            return redirect('core:accueil')
        
        # Créer l'abonnement
        abonne = AbonneNewsletter.objects.create(
            email=email,
            nom=nom
        )
        
        # Email de confirmation
        try:
            send_mail(
                "Confirmation d'abonnement - Ma Boutique",
                f"""
Bonjour {nom or 'Cher client'},

Merci de vous être abonné à la newsletter de Ma Boutique !

Vous recevrez désormais nos promotions et nouveautés.

Pour vous désabonner, cliquez sur ce lien :
{request.build_absolute_uri(f'/newsletter/desabonnement/{abonne.token_desabonnement}/')}

À bientôt,
L'équipe Ma Boutique
                """,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Erreur d'envoi: {e}")
        
        messages.success(request, "✅ Abonnement réussi ! Vérifiez votre email.")
        return redirect('core:accueil')
    
    return render(request, 'core/newsletter_abonnement.html')


def newsletter_desabonnement(request, token):
    """Désabonnement de la newsletter"""
    try:
        abonne = AbonneNewsletter.objects.get(token_desabonnement=token, actif=True)
    except AbonneNewsletter.DoesNotExist:
        messages.error(request, "❌ Lien de désabonnement invalide.")
        return redirect('core:accueil')
    
    if request.method == 'POST':
        abonne.actif = False
        abonne.save()
        messages.success(request, "✅ Vous êtes désabonné de la newsletter.")
        return redirect('core:accueil')
    
    return render(request, 'core/newsletter_desabonnement.html', {'abonne': abonne})


def newsletter_creer(request):
    """Créer un email de newsletter (pour les admins)"""
    if not request.user.is_staff:
        messages.error(request, "⛔ Accès réservé à l'administration.")
        return redirect('core:accueil')
    
    if request.method == 'POST':
        sujet = request.POST.get('sujet', '').strip()
        contenu = request.POST.get('contenu', '').strip()
        
        if not sujet or not contenu:
            messages.error(request, "❌ Tous les champs sont obligatoires.")
            return render(request, 'core/newsletter_creer.html')
        
        email = EmailNewsletter.objects.create(
            sujet=sujet,
            contenu=contenu
        )
        
        messages.success(request, f"✅ Email '{sujet}' créé ! Vous pouvez l'envoyer depuis l'admin.")
        return redirect('core:stats_admin')
    
    return render(request, 'core/newsletter_creer.html')