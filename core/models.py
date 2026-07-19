from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.files import File
from io import BytesIO
import qrcode
import random
import string
import uuid
# ============================================
# 1. CATÉGORIE
# ============================================
class Categorie(models.Model):
    """Catégorie de produits"""
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"



# ============================================
# 2. SOCIÉTÉ (NOUVEAU)
# ============================================
class Societe(models.Model):
    """Entreprise partenaire (vendeur)"""
    
    # Identité
    nom = models.CharField(max_length=200, unique=True)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20)
    adresse = models.TextField(blank=True)
    ville = models.CharField(max_length=100, blank=True)
    
    # Compte utilisateur (connexion)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='societe'
    )
    
    # Logo
    logo = models.ImageField(upload_to='societes/logos/', blank=True, null=True)
    
    # Commission par défaut
    commission_par_defaut = models.IntegerField(
        default=15,
        help_text="Commission par défaut en % (10, 15, 18 ou 20)"
    )
    
    # Statut
    actif = models.BooleanField(default=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nom
    
    @property
    def total_ventes(self):
        """Total des ventes de la société"""
        from .models import LigneCommande
        total = 0
        for produit in self.produits.all():
            for ligne in produit.lignecommande_set.all():
                total += ligne.quantite * ligne.prix_unitaire
        return total
    
    @property
    def total_commissions(self):
        """Total des commissions générées"""
        from .models import LigneCommande
        total = 0
        for produit in self.produits.all():
            for ligne in produit.lignecommande_set.all():
                # Calculer la commission
                taux = produit.commission_taux / 100
                total += (ligne.quantite * ligne.prix_unitaire) * taux
        return int(total)
    
    @property
    def total_reversement(self):
        """Total à reverser à la société"""
        return self.total_ventes - self.total_commissions
    
    class Meta:
        verbose_name = "Société"
        verbose_name_plural = "Sociétés"


# ============================================
# 3. PRODUIT (MODIFIÉ)
# ============================================
class Produit(models.Model):
    """Produit à vendre"""
    
    # Informations
    nom = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.IntegerField(help_text="Prix en FCFA")
    stock = models.IntegerField(default=0)
    
    # 🔥 NOUVEAU : Société vendeuse
    societe = models.ForeignKey(
        Societe,
        on_delete=models.CASCADE,
        related_name='produits',
        null=True,
        blank=True
    )
    
    # Catégorie
    categorie = models.ForeignKey(
        Categorie, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='produits'
    )
    
    # Image
    image = models.ImageField(upload_to='produits/', blank=True, null=True)
    
    # QR Code
    qr_code_texte = models.CharField(max_length=200, blank=True,null=True)
    qr_code_image = models.ImageField(upload_to='qrcodes/produits/', blank=True, null=True)
    reference_unique = models.CharField(max_length=20, unique=True, blank=True, null=True)
    
    # Commission (calculée automatiquement)
    commission_taux = models.IntegerField(
        default=15,
        help_text="Taux de commission appliqué (10, 15, 18 ou 20%)"
    )
    commission_montant = models.IntegerField(
        default=0,
        help_text="Montant de la commission en FCFA (calculé automatiquement)"
    )
    
    # Statut
    en_vente = models.BooleanField(default=True)
    approuve = models.BooleanField(default=True, help_text="Approuvé par l'administrateur")
    date_ajout = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nom} - {self.societe.nom if self.societe else 'Sans société'}"
    
    def est_disponible(self):
        return self.stock > 0 and self.en_vente and self.approuve
    
    def generer_reference_unique(self):
        """Génère une référence unique pour le produit"""
        if not self.reference_unique:
            lettres = string.ascii_uppercase + string.digits
            code = ''.join(random.choices(lettres, k=6))
            self.reference_unique = f"PROD-{code}"
        return self.reference_unique
    
    def calculer_commission(self):
        """Calcule automatiquement la commission en fonction du prix"""
        # Algorithme de commission progressive
        if self.prix <= 50000:
            taux = 10  # 10% pour les petits prix
        elif self.prix <= 200000:
            taux = 15  # 15% pour les prix moyens
        elif self.prix <= 500000:
            taux = 18  # 18% pour les prix élevés
        else:
            taux = 20  # 20% pour les très grands prix
        
        self.commission_taux = taux
        self.commission_montant = int((self.prix * taux) / 100)
        return self.commission_montant
    
    def generer_qr_code(self):
        """Génère le QR code pour le produit"""
        if not self.reference_unique:
            self.generer_reference_unique()
        
        # Données du QR code
        qr_data = f"PRODUIT: {self.reference_unique}\n"
        qr_data += f"NOM: {self.nom}\n"
        qr_data += f"PRIX: {self.prix} FCFA\n"
        qr_data += f"SOCIETE: {self.societe.nom if self.societe else 'N/A'}"
        
        # Générer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Créer l'image
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        # Sauvegarder
        filename = f"qr_{self.reference_unique}.png"
        self.qr_code_image.save(filename, File(buffer), save=False)
        self.qr_code_texte = qr_data
        return self.qr_code_image
    
    def save(self, *args, **kwargs):
        # Générer la référence unique
        if not self.reference_unique:
            self.generer_reference_unique()
        
        # Calculer la commission automatiquement
        self.calculer_commission()
        
        # Générer le QR code
        if not self.qr_code_image:
            self.generer_qr_code()
        
        super().save(*args, **kwargs)
    def get_prix_avec_promo(self):
     """Retourne le prix avec promotion si disponible"""
     try:
        promo = self.promotion
        if promo.est_active:
            return int(promo.prix_promo)
     except Promotion.DoesNotExist:
        pass
     return self.prix

    def get_pourcentage_promo(self):
     """Retourne le pourcentage de promotion si disponible"""
     try:
        promo = self.promotion
        if promo.est_active:
            return promo.pourcentage
     except Promotion.DoesNotExist:
        pass
     return 0

    def est_en_promo(self):
     """Vérifie si le produit est en promotion"""
     try:
        promo = self.promotion
        return promo.est_active
     except Promotion.DoesNotExist:
        return False
    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['-date_ajout']


# ============================================
# 3. PANIER
# ============================================
class Panier(models.Model):
    """Panier d'un utilisateur"""
    utilisateur = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='panier'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Panier de {self.utilisateur.username}"
    
    def get_total(self):
        """Calcule le total du panier"""
        total = 0
        for article in self.articles.all():
            total += article.quantite * article.prix_unitaire
        return total
    
    def get_nb_articles(self):
        """Nombre total d'articles dans le panier"""
        return sum(article.quantite for article in self.articles.all())
    
    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"


class ArticlePanier(models.Model):
    """Un produit dans le panier"""
    panier = models.ForeignKey(
        Panier,
        on_delete=models.CASCADE,
        related_name='articles'
    )
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE
    )
    quantite = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    prix_unitaire = models.IntegerField(help_text="Prix au moment de l'ajout")
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Un produit ne peut être qu'une fois dans le panier
        unique_together = ('panier', 'produit')
        verbose_name = "Article du panier"
        verbose_name_plural = "Articles du panier"
    
    def __str__(self):
        return f"{self.produit.nom} x {self.quantite}"
    
    def get_total(self):
        """Total pour cette ligne"""
        return self.quantite * self.prix_unitaire


# ============================================
# 4. COMMANDE
# ============================================
class Commande(models.Model):
    """Commande d'un client"""
    
    MODE_PAIEMENT = [
        ('mobile_money', 'Mobile Money (Orange/MTN)'),
        ('boutique', 'Paiement en boutique'),
    ]
    
    STATUT = [
        ('en_attente', 'En attente de paiement'),
        ('payee', 'Payée'),
        ('en_preparation', 'En préparation'),
        ('expediee', 'Expédiée'),
        ('livree', 'Livrée'),
        ('annulee', 'Annulée'),
    ]
    
    # Client
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='commandes'
    )
    
    # Informations de livraison
    nom_complet = models.CharField(max_length=200)
    telephone = models.CharField(max_length=20)
    adresse_livraison = models.TextField()
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=20, blank=True)
    
    # Paiement
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT)
    payee = models.BooleanField(default=False)
    reference_paiement = models.CharField(max_length=100, blank=True)
    
    # Totaux
    total = models.IntegerField()
    
    # Statut
    statut = models.CharField(max_length=20, choices=STATUT, default='en_attente')
    
    # Dates
    date_commande = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Commande #{self.id} - {self.client.username}"
    
    def get_total_par_article(self):
        """Retourne le total par article"""
        return [(ligne.produit.nom, ligne.quantite * ligne.prix_unitaire) for ligne in self.lignes.all()]
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-date_commande']


class LigneCommande(models.Model):
    """Un produit dans une commande"""
    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,
        related_name='lignes'
    )
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE
    )
    quantite = models.IntegerField()
    prix_unitaire = models.IntegerField()
    
    def __str__(self):
        return f"{self.produit.nom} x {self.quantite}"
    
    def get_total(self):
        return self.quantite * self.prix_unitaire
    
    class Meta:
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"



class TokenReinitialisation(models.Model):
    """Token pour la réinitialisation de mot de passe"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField()
    utilise = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Token de {self.user.username} - {self.token[:10]}..."
    
    def est_valide(self):
        """Vérifie si le token est encore valide"""
        from django.utils import timezone
        return not self.utilise and timezone.now() < self.date_expiration
    
    class Meta:
        verbose_name = "Token de réinitialisation"
        verbose_name_plural = "Tokens de réinitialisation"

     
        
class Favori(models.Model):
    """Produits favoris d'un utilisateur"""
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoris')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='favoris')
    date_ajout = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        unique_together = ('utilisateur', 'produit')
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.produit.nom}"
    

class Notation(models.Model):
    """Notation d'un produit par un utilisateur"""
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='notations')
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notations')
    note = models.IntegerField(choices=[(1, '1★'), (2, '2★'), (3, '3★'), (4, '4★'), (5, '5★')])
    commentaire = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('produit', 'utilisateur')
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.produit.nom} - {self.note}★"


                 
class MessageChat(models.Model):
    expediteur = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE, 
        related_name='messages_envoyes'
    )
    destinataire = models.ForeignKey(
        'auth.User', 
        on_delete=models.CASCADE, 
        related_name='messages_recus', 
        null=True, 
        blank=True
    )
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)
    date_lu = models.DateTimeField(null=True, blank=True)
    conversation_id = models.CharField(max_length=100, db_index=True)
    
    def __str__(self):
        return f"{self.expediteur.username} -> {self.destinataire.username if self.destinataire else 'support'}: {self.contenu[:30]}"
    
    class Meta:
        ordering = ['date_envoi']

       


class DemandeDevis(models.Model):
    """Demande de devis d'un client"""
    nom = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    produit = models.ForeignKey(
        'Produit', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='demandes_devis'
    )
    message = models.TextField()
    date_demande = models.DateTimeField(auto_now_add=True)
    traite = models.BooleanField(default=False)
    date_traitement = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Devis de {self.nom} - {self.produit.nom if self.produit else 'Général'}"
    
    class Meta:
        verbose_name = "Demande de devis"
        verbose_name_plural = "Demandes de devis"
        ordering = ['-date_demande']



    
class Promotion(models.Model):
    """Promotion sur un produit"""
    produit = models.OneToOneField(
        Produit,
        on_delete=models.CASCADE,
        related_name='promotion'
    )
    pourcentage = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Pourcentage de réduction (1-100)"
    )
    date_debut = models.DateField()
    date_fin = models.DateField()
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.produit.nom} - {self.pourcentage}%"
    
    @property
    def prix_promo(self):
        """Calcule le prix après réduction"""
        return self.produit.prix * (1 - self.pourcentage / 100)
    
    @property
    def est_active(self):
        """Vérifie si la promotion est active"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.actif and self.date_debut <= today <= self.date_fin
    
    class Meta:
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"
        ordering = ['-date_creation']




class AbonneNewsletter(models.Model):
    """Abonné à la newsletter"""
    email = models.EmailField(unique=True)
    nom = models.CharField(max_length=100, blank=True, help_text="Optionnel")
    date_abonnement = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)
    token_desabonnement = models.CharField(max_length=64, unique=True, blank=True)
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        if not self.token_desabonnement:
            import secrets
            self.token_desabonnement = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Abonné à la newsletter"
        verbose_name_plural = "Abonnés à la newsletter"
        ordering = ['-date_abonnement']


class EmailNewsletter(models.Model):
    """Email envoyé à la newsletter"""
    sujet = models.CharField(max_length=200)
    contenu = models.TextField()
    envoye_le = models.DateTimeField(auto_now_add=True)
    envoye = models.BooleanField(default=False)
    nb_destinataires = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.sujet} - {self.envoye_le.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = "Email newsletter"
        verbose_name_plural = "Emails newsletter"
        ordering = ['-envoye_le']