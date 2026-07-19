from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Categorie, Produit, Panier, ArticlePanier, Commande, LigneCommande,Societe

# Réenregistrer User dans l'admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prix', 'stock', 'categorie', 'en_vente', 'est_disponible', 'afficher_qr_code')
    list_filter = ('categorie', 'en_vente')
    search_fields = ('nom', 'description', 'reference_unique')
    list_editable = ('prix', 'stock', 'en_vente')
    readonly_fields = ('reference_unique', 'afficher_qr_code', 'qr_code_texte')
    
    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'description', 'prix', 'stock', 'categorie')
        }),
        ('Images', {
            'fields': ('image',)
        }),
        ('QR Code', {
            'fields': ('reference_unique', 'afficher_qr_code', 'qr_code_texte', 'qr_code_image'),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('en_vente',)
        }),
    )
    
    def afficher_qr_code(self, obj):
        """Affiche le QR code dans l'admin"""
        if obj.qr_code_image:
            return format_html(
                '<img src="{}" width="100" height="100" style="border: 1px solid #ddd; border-radius: 8px;" />',
                obj.qr_code_image.url
            )
        return "❌ Non généré"
    afficher_qr_code.short_description = "QR Code"
    
    def save_model(self, request, obj, form, change):
        """Sauvegarde avec génération du QR code"""
        if not change or not obj.qr_code_image:
            obj.generer_reference_unique()
            obj.generer_qr_code()
        super().save_model(request, obj, form, change)


@admin.register(Panier)
class PanierAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'date_creation', 'get_nb_articles', 'get_total')
    search_fields = ('utilisateur__username', 'utilisateur__email')
    
    def get_nb_articles(self, obj):
        return obj.get_nb_articles()
    get_nb_articles.short_description = "Nombre d'articles"
    
    def get_total(self, obj):
        return f"{obj.get_total()} FCFA"
    get_total.short_description = "Total"


@admin.register(ArticlePanier)
class ArticlePanierAdmin(admin.ModelAdmin):
    list_display = ('panier', 'produit', 'quantite', 'prix_unitaire', 'get_total')
    search_fields = ('panier__utilisateur__username', 'produit__nom')
    
    def get_total(self, obj):
        return f"{obj.get_total()} FCFA"
    get_total.short_description = "Total"


class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 0
    readonly_fields = ('produit', 'quantite', 'prix_unitaire')
    can_delete = False


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'total', 'mode_paiement', 'payee', 'statut', 'date_commande')
    list_filter = ('statut', 'payee', 'mode_paiement')
    search_fields = ('client__username', 'client__email', 'nom_complet', 'telephone')
    readonly_fields = ('date_commande', 'date_modification')
    inlines = [LigneCommandeInline]
    
    fieldsets = (
        ('Client', {
            'fields': ('client', 'nom_complet', 'telephone', 'adresse_livraison', 'ville', 'code_postal')
        }),
        ('Paiement', {
            'fields': ('mode_paiement', 'payee', 'reference_paiement')
        }),
        ('Totaux', {
            'fields': ('total',)
        }),
        ('Statut', {
            'fields': ('statut',)
        }),
        ('Dates', {   
            'fields': ('date_commande', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marquer_payee', 'marquer_expediee', 'marquer_livree']
    
    def marquer_payee(self, request, queryset):
        queryset.update(payee=True, statut='payee')
    marquer_payee.short_description = "Marquer comme payée"
    
    def marquer_expediee(self, request, queryset):
        queryset.update(statut='expediee')
    marquer_expediee.short_description = "Marquer comme expédiée"
    
    def marquer_livree(self, request, queryset):
        queryset.update(statut='livree')
    marquer_livree.short_description = "Marquer comme livrée"


@admin.register(LigneCommande)
class LigneCommandeAdmin(admin.ModelAdmin):
    list_display = ('commande', 'produit', 'quantite', 'prix_unitaire', 'get_total')
    search_fields = ('commande__id', 'produit__nom')
    
    def get_total(self, obj):
        return f"{obj.get_total()} FCFA"
    get_total.short_description = "Total"

admin.site.register(Societe)

from .models import DemandeDevis

@admin.register(DemandeDevis)
class DemandeDevisAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'telephone', 'produit', 'date_demande', 'traite')
    list_filter = ('traite', 'date_demande')
    search_fields = ('nom', 'email', 'telephone', 'produit__nom')
    list_editable = ('traite',)
    readonly_fields = ('date_demande',)
    
    actions = ['marquer_traite']
    
    def marquer_traite(self, request, queryset):
        queryset.update(traite=True)
    marquer_traite.short_description = "Marquer comme traité"



from .models import Promotion

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('produit', 'pourcentage', 'prix_promo', 'date_debut', 'date_fin', 'est_active', 'actif')
    list_filter = ('actif', 'date_debut', 'date_fin')
    search_fields = ('produit__nom',)
    list_editable = ('pourcentage', 'actif')
    readonly_fields = ('prix_promo',)
    
    fieldsets = (
        ('Informations', {
            'fields': ('produit', 'pourcentage')
        }),
        ('Période', {
            'fields': ('date_debut', 'date_fin', 'actif')
        }),
        ('Calcul', {
            'fields': ('prix_promo',),
            'classes': ('collapse',)
        }),
    )
    
    def prix_promo(self, obj):
        return f"{obj.prix_promo:.0f} FCFA"
    prix_promo.short_description = "Prix promo"


from .models import AbonneNewsletter, EmailNewsletter

@admin.register(AbonneNewsletter)
class AbonneNewsletterAdmin(admin.ModelAdmin):
    list_display = ('email', 'nom', 'date_abonnement', 'actif')
    list_filter = ('actif', 'date_abonnement')
    search_fields = ('email', 'nom')
    list_editable = ('actif',)
    actions = ['exporter_csv']
    
    def exporter_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="abonnes_newsletter.csv"'
        writer = csv.writer(response)
        writer.writerow(['Email', 'Nom', 'Date abonnement', 'Actif'])
        for abonne in queryset:
            writer.writerow([abonne.email, abonne.nom, abonne.date_abonnement, abonne.actif])
        return response
    exporter_csv.short_description = "Exporter les abonnés sélectionnés en CSV"


@admin.register(EmailNewsletter)
class EmailNewsletterAdmin(admin.ModelAdmin):
    list_display = ('sujet', 'envoye_le', 'envoye', 'nb_destinataires')
    list_filter = ('envoye', 'envoye_le')
    search_fields = ('sujet', 'contenu')
    readonly_fields = ('envoye_le', 'nb_destinataires')
    
    actions = ['envoyer_newsletter']
    
    def envoyer_newsletter(self, request, queryset):
        from django.core.mail import send_mail
        from django.conf import settings
        
        for email in queryset.filter(envoye=False):
            abonnes = AbonneNewsletter.objects.filter(actif=True)
            
            for abonne in abonnes:
                lien_desabonnement = request.build_absolute_uri(
                    f"/newsletter/desabonnement/{abonne.token_desabonnement}/"
                )
                
                contenu_personnalise = email.contenu.replace(
                    '[LIEN_DESABONNEMENT]', lien_desabonnement
                )
                contenu_personnalise = contenu_personnalise.replace(
                    '[NOM]', abonne.nom or 'Cher client'
                )
                
                try:
                    send_mail(
                        email.sujet,
                        contenu_personnalise,
                        settings.DEFAULT_FROM_EMAIL,
                        [abonne.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Erreur d'envoi à {abonne.email}: {e}")
            
            email.envoye = True
            email.nb_destinataires = abonnes.count()
            email.save()
        
        self.message_user(request, f"Newsletter envoyée à {email.nb_destinataires} abonnés.")
    envoyer_newsletter.short_description = "Envoyer la newsletter sélectionnée"