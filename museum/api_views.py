# museum/api_views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Order, ScanLog

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@csrf_exempt
@require_POST
def validate_ticket(request):
    """
    Endpoint API pour valider un ticket par code-barres EAN13.
    Enregistre un log de scan.
    """
    try:
        data = json.loads(request.body)
        barcode = data.get('barcode', '').strip()
        scan_location = data.get('lieu', 'Scanner').strip()
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)

    if not barcode:
        return JsonResponse({'success': False, 'error': 'Code-barres manquant'}, status=400)

    # Fonction utilitaire pour logger
    def log_scan(order, success, message):
        ScanLog.objects.create(
            order=order,
            success=success,
            message=message,
            scan_location=scan_location,
            ip_address=get_client_ip(request)
        )

    try:
        order = Order.objects.get(transaction_id=barcode, paid=True)
    except Order.DoesNotExist:
        # Ticket non trouvé -> on ne peut pas logger car pas d'order
        return JsonResponse({'success': False, 'error': 'Ticket invalide ou non payé'}, status=404)

    # Vérifier si déjà validé
    if order.validated_at is not None:
        log_scan(order, False, "Ticket déjà utilisé")
        return JsonResponse({
            'success': False,
            'error': 'Ticket déjà utilisé',
            'validated_at': order.validated_at.isoformat(),
            'validation_count': order.validation_count
        }, status=409)

    # Première validation
    order.validated_at = timezone.now()
    order.validation_count = 1
    order.save()
    log_scan(order, True, "Ticket valide - accès autorisé")

    items = [{'name': item.name, 'quantity': item.quantity} for item in order.items.all()]
    return JsonResponse({
        'success': True,
        'message': 'Ticket valide - accès autorisé',
        'order_id': order.id,
        'total_amount': order.total_amount,
        'items': items,
        'validated_at': order.validated_at.isoformat()
    })