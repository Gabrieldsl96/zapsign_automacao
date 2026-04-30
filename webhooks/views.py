import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def receive_webhook(request):
    """
    Endpoint que recebe webhooks da ZapSign.

    A ZapSign espera status 200 como confirmação; qualquer outro código
    faz ela retentar o envio gerando duplicidades.
    """
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "JSON inválido"}, status=400)

    event_type = payload.get("event_type")
    logger.info("Webhook recebido — evento: %s", event_type)

    if event_type == "doc_signed":
        _handle_doc_signed(payload)

    return JsonResponse({"status": "ok"})


# ──────────────────────────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────────────────────────


def _handle_doc_signed(payload):
    """
    Processa o evento doc_signed.

    - Atualiza o status do documento e dos signatários no banco.
    - Se o documento 1 foi totalmente assinado (status == 'signed'),
      cria o documento 2 automaticamente na ZapSign.
    - Se o documento 2 foi totalmente assinado, marca o fluxo como 'completed'.
    """
    from documents.models import Signer, ZapSignDocument
    from documents.services import create_zapsign_document

    doc_token = payload.get("token")
    doc_status = payload.get(
        "status"
    )  # "signed" = todos assinaram; "pending" = parcial

    if not doc_token:
        logger.warning("Webhook doc_signed recebido sem token de documento")
        return

    try:
        doc = ZapSignDocument.objects.select_related("flow").get(
            zapsign_token=doc_token
        )
    except ZapSignDocument.DoesNotExist:
        logger.warning('Documento com token "%s" não encontrado no banco', doc_token)
        return

    # Atualiza o signatário que acabou de assinar
    signer_who_signed = payload.get("signer_who_signed") or {}
    signer_token = signer_who_signed.get("token")
    if signer_token:
        Signer.objects.filter(document=doc, zapsign_token=signer_token).update(
            status="signed"
        )

    if doc_status != "signed":
        # Nem todos os signatários assinaram ainda — aguarda
        logger.info(
            'Documento "%s" parcialmente assinado; aguardando os demais signatários',
            doc.name,
        )
        return

    # Todos assinaram — atualiza status do documento
    doc.status = "signed"
    doc.save(update_fields=["status"])

    flow = doc.flow

    if doc.order == 1:
        logger.info(
            'Documento 1 do fluxo "%s" assinado. Criando Documento 2...', flow.name
        )
        try:
            doc2 = flow.documents.get(order=2)
            create_zapsign_document(doc2)
            flow.status = "doc2_pending"
            flow.save(update_fields=["status"])
            logger.info('Documento 2 criado com sucesso para o fluxo "%s"', flow.name)
        except ZapSignDocument.DoesNotExist:
            logger.error("Documento 2 não encontrado para o fluxo id=%s", flow.pk)
        except Exception as exc:
            logger.error(
                "Erro ao criar Documento 2 para o fluxo id=%s: %s", flow.pk, exc
            )

    elif doc.order == 2:
        flow.status = "completed"
        flow.save(update_fields=["status"])
        logger.info(
            'Fluxo "%s" concluído com todos os documentos assinados!', flow.name
        )
