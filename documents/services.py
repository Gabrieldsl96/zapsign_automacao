import base64
import logging

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

ZAPSIGN_API_URL = "https://sandbox.api.zapsign.com.br/api/v1"


def create_zapsign_document(document):
    """
    Cria um documento na API da ZapSign e atualiza o model com os dados retornados.

    Args:
        document: instância de ZapSignDocument com signers já cadastrados no banco.

    Returns:
        dict com o JSON de resposta da ZapSign.

    Raises:
        requests.HTTPError: se a API retornar erro HTTP.
    """
    headers = {
        "Authorization": f"Bearer {settings.ZAPSIGN_API_TOKEN}",
        "Content-Type": "application/json",
    }

    signers_data = []
    for signer in document.signers.all():
        signer_payload = {"name": signer.name}
        if signer.email:
            signer_payload["email"] = signer.email
            signer_payload["send_automatic_email"] = True
        signers_data.append(signer_payload)

    payload = {
        "name": document.name,
        "base64_pdf": _file_to_base64(document.pdf_file),
        "folder_path": f"/{document.flow.folder}/{document.flow.name}",
        "signers": signers_data,
    }

    logger.info(
        'Criando documento "%s" na ZapSign (fluxo %s)', document.name, document.flow_id
    )

    response = requests.post(
        f"{ZAPSIGN_API_URL}/docs/",
        json=payload,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    # Atualiza o documento com o token e status retornados pela ZapSign
    document.zapsign_token = data["token"]
    # Doc 2 é enviado sem aguardar assinatura
    document.status = "sent" if document.order == 2 else "pending"
    document.created_at = timezone.now()
    document.save()

    # Atualiza cada signatário com token e link de assinatura
    signers = list(document.signers.all())
    for i, signer_data in enumerate(data.get("signers", [])):
        if i < len(signers):
            signers[i].zapsign_token = signer_data.get("token", "")
            signers[i].sign_url = signer_data.get("sign_url", "")
            signers[i].save()

    logger.info(
        'Documento "%s" criado com token %s', document.name, document.zapsign_token
    )
    return data


def _file_to_base64(file_field):
    """Lê o arquivo do FileField e retorna a string base64 (sem prefixo data:...)."""
    file_field.open("rb")
    try:
        return base64.b64encode(file_field.read()).decode("utf-8")
    finally:
        file_field.close()
