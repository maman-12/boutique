def calculer_commission(prix, taux=None):
    """
    Calcule la commission en fonction du prix et du taux
    
    Args:
        prix (int): Prix du produit en FCFA
        taux (int, optional): Taux de commission personnalisé
    
    Returns:
        dict: {
            'taux': int,  # Taux appliqué en %
            'montant': int,  # Montant de la commission en FCFA
            'reversement': int,  # Montant à reverser au vendeur
            'bareme': str  # Barème appliqué
        }
    """
    if taux is None:
        # Algorithme de commission progressive
        if prix <= 50000:
            taux = 10
            bareme = "Petit prix (< 50 000 FCFA)"
        elif prix <= 200000:
            taux = 15
            bareme = "Prix moyen (50 000 - 200 000 FCFA)"
        elif prix <= 500000:
            taux = 18
            bareme = "Prix élevé (200 000 - 500 000 FCFA)"
        else:
            taux = 20
            bareme = "Très grand prix (> 500 000 FCFA)"
    else:
        bareme = f"Taux fixe de {taux}%"
    
    montant = int((prix * taux) / 100)
    reversement = prix - montant
    
    return {
        'taux': taux,
        'montant': montant,
        'reversement': reversement,
        'bareme': bareme
    }


def calculer_commission_commande(lignes_commande):
    """
    Calcule les commissions pour toute une commande
    
    Args:
        lignes_commande (list): Liste des objets LigneCommande
    
    Returns:
        dict: {
            'total_commission': int,
            'details_par_societe': {
                'societe_nom': {
                    'total': int,
                    'commission': int,
                    'reversement': int
                }
            }
        }
    """
    total_commission = 0
    details_par_societe = {}
    
    for ligne in lignes_commande:
        produit = ligne.produit
        societe = produit.societe
        
        if societe:
            nom = societe.nom
            if nom not in details_par_societe:
                details_par_societe[nom] = {
                    'total': 0,
                    'commission': 0,
                    'reversement': 0
                }
            
            total_ligne = ligne.quantite * ligne.prix_unitaire
            commission_ligne = (total_ligne * produit.commission_taux) / 100
            
            details_par_societe[nom]['total'] += total_ligne
            details_par_societe[nom]['commission'] += int(commission_ligne)
            details_par_societe[nom]['reversement'] += int(total_ligne - commission_ligne)
            total_commission += int(commission_ligne)
    
    return {
        'total_commission': total_commission,
        'details_par_societe': details_par_societe
    }