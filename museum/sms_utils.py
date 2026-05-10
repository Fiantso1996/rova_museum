import africastalking
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialiser le SDK une seule fois au démarrage
try:
    africastalking.initialize(
        settings.AFRICASTALKING_USERNAME,
        settings.AFRICASTALKING_API_KEY
    )
    sms_service = africastalking.SMS
    logger.info("Africa's Talking SDK initialisé avec succès.")
except Exception as e:
    logger.error(f"Échec de l'initialisation du SDK Africa's Talking: {e}")
    sms_service = None

def send_sms_confirmation(phone_number, order):
    """
    Envoie un SMS de confirmation via l'API Africa's Talking.
    """
    if not sms_service:
        logger.error("Service SMS non disponible.")
        return False

    # S'assurer que le numéro est au format international (ex: +261...)
    if not phone_number.startswith('+'):
        # Si le numéro commence par 0, on le remplace par +261 (indicatif Madagascar)
        if phone_number.startswith('0'):
            phone_number = '+261' + phone_number[1:]
        else:
            phone_number = '+' + phone_number

    message = (
        f"Musee Rova: Paiement confirme! Commande #{order.id}. "
        f"Total: {order.total_amount} Ar. Code EAN13: {order.transaction_id}. "
        f"Presentez ce code a l'entree. Merci!"
    )

    try:
        # Pour les tests, utilisez le sender_id "Sandbox"
        sender_id = "Sandbox" if settings.AFRICASTALKING_USERNAME == 'sandbox' else None
        
        # Envoi du SMS. 
        # La méthode `send` prend le message, la liste des destinataires et le sender_id.
        response = sms_service.send(message, [phone_number], sender_id)[reference:5]
        logger.info(f"SMS envoyé avec succès à {phone_number}. Réponse: {response}")
        return True
    except Exception as e:
        logger.error(f"Échec de l'envoi du SMS à {phone_number}: {e}")
        return False
    
# Dans museum/sms_utils.py
def format_phone_number(raw_number):
    """Nettoie et formate un numéro malgache au format international."""
    import re
    # Supprime tous les caractères non numériques sauf le '+'
    clean_number = re.sub(r'[^\d+]', '', raw_number)
    
    # Si le numéro commence par '0', on le remplace par '+261'
    if clean_number.startswith('0'):
        return '+261' + clean_number[1:]
    # Si le numéro ne commence pas par '+', on l'ajoute
    elif not clean_number.startswith('+'):
        return '+' + clean_number
    return clean_number