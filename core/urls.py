from django.urls import path
from . import views

app_name = 'core'
   
urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
     # Produits
    path('produits/', views.liste_produits, name='produits'),
    path('produit/<int:produit_id>/', views.detail_produit, name='detail_produit'),
         
    # Panier        
    path('panier/', views.panier, name='panier'),
    path('panier/ajouter/<int:produit_id>/', views.ajouter_panier, name='ajouter_panier'),
    path('panier/supprimer/<int:article_id>/', views.supprimer_article_panier, name='supprimer_article'),
    path('panier/modifier/<int:article_id>/', views.modifier_quantite_panier, name='modifier_quantite'),
    path('panier/vider/', views.vider_panier, name='vider_panier'),
    
    # Commandes              
    path('commande/', views.passer_commande, name='commande'),
    path('confirmation/<int:commande_id>/', views.confirmation_commande, name='confirmation'),
    path('historique/', views.historique_commandes, name='historique'),
                                                    
       # Réinitialisation mot de passe
    path('mot-de-passe-oublie/', views.mot_de_passe_oublie, name='mot_de_passe_oublie'),
    path('reinitialiser/<str:token>/', views.reinitialiser_mot_de_passe, name='reinitialiser_mot_de_passe'),

     path('favoris/', views.mes_favoris, name='favoris'),
path('favoris/ajouter/<int:produit_id>/', views.ajouter_favori, name='ajouter_favori'),

    path('produit/noter/<int:produit_id>/', views.noter_produit, name='noter_produit'),
    path('chat/br/', views.chat, name='chat'),
    path('profile/',views.profile,name="profil"),
    path('chat/', views.chat_interface, name='chat_interface'),
    path('panier/count/', views.panier_count, name='panier_count'),

     
# Newsletter
path('newsletter/', views.newsletter_abonnement, name='newsletter_abonnement'),
path('newsletter/desabonnement/<str:token>/', views.newsletter_desabonnement, name='newsletter_desabonnement'),
path('newsletter/creer/', views.newsletter_creer, name='newsletter_creer'),

# Ajouter dans urlpatterns
path('entreprise/dashboard/', views.dashboard_entreprise, name='dashboard_entreprise'),
path('entreprise/produits/', views.liste_produits_entreprise, name='liste_produits_entreprise'),
path('entreprise/produit/ajouter/', views.ajouter_produit, name='ajouter_produit'),
path('entreprise/produit/modifier/<int:produit_id>/', views.modifier_produit, name='modifier_produit'),
path('entreprise/produit/supprimer/<int:produit_id>/', views.supprimer_produit, name='supprimer_produit'),
# Ajouter dans urlpatterns
path('entreprise/inscription/', views.inscription_entreprise, name='inscription_entreprise'),
path('entreprise/connexion/', views.connexion_entreprise, name='connexion_entreprise'),
path('devis/', views.demande_devis, name='demande_devis'),
path('devis/<int:produit_id>/', views.demande_devis, name='demande_devis_produit'),
path('mes-devis/', views.mes_devis, name='mes_devis'),
path('stats/', views.stats_admin, name='stats_admin'),
]