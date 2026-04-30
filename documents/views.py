from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .models import DocumentFlow, Signer, ZapSignDocument
from .services import create_zapsign_document


def index(request):
    """Lista todos os fluxos de documentos."""
    flows = DocumentFlow.objects.prefetch_related("documents__signers").order_by(
        "-created_at"
    )
    return render(request, "documents/index.html", {"flows": flows})


def create_flow(request):
    """Formulário para criar um novo fluxo com 2 documentos encadeados."""
    if request.method == "POST":
        flow_name = request.POST.get("flow_name", "").strip()

        doc1_name = request.POST.get("doc1_name", "").strip()
        doc1_pdf_file = request.FILES.get("doc1_pdf_file")
        doc1_signer_names = request.POST.getlist("doc1_signer_name")
        doc1_signer_emails = request.POST.getlist("doc1_signer_email")

        doc2_name = request.POST.get("doc2_name", "").strip()
        doc2_pdf_file = request.FILES.get("doc2_pdf_file")
        doc2_signer_names = request.POST.getlist("doc2_signer_name")
        doc2_signer_emails = request.POST.getlist("doc2_signer_email")

        errors = _validate_flow_data(
            flow_name,
            doc1_name,
            doc1_pdf_file,
            doc1_signer_names,
            doc2_name,
            doc2_pdf_file,
            doc2_signer_names,
        )

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(
                request, "documents/create_flow.html", {"post_data": request.POST}
            )

        # Cria o fluxo e os dois documentos no banco
        flow = DocumentFlow.objects.create(name=flow_name)

        doc1 = ZapSignDocument.objects.create(
            flow=flow, order=1, name=doc1_name, pdf_file=doc1_pdf_file
        )
        _create_signers(doc1, doc1_signer_names, doc1_signer_emails)

        # Documento 2 fica salvo no banco mas só é enviado à ZapSign após doc1 assinado
        doc2 = ZapSignDocument.objects.create(
            flow=flow, order=2, name=doc2_name, pdf_file=doc2_pdf_file
        )
        _create_signers(doc2, doc2_signer_names, doc2_signer_emails)

        # Envia documento 1 para a ZapSign agora
        try:
            create_zapsign_document(doc1)
            messages.success(
                request,
                f'Fluxo "{flow_name}" criado! Documento 1 enviado para assinatura. '
                "O Documento 2 será gerado automaticamente após a assinatura do Documento 1.",
            )
        except Exception as exc:
            flow.delete()
            messages.error(request, f"Erro ao criar documento na ZapSign: {exc}")
            return render(
                request, "documents/create_flow.html", {"post_data": request.POST}
            )

        return redirect("documents:flow_detail", pk=flow.pk)

    return render(request, "documents/create_flow.html", {})


def flow_detail(request, pk):
    """Detalha um fluxo com seus documentos e links de assinatura."""
    flow = get_object_or_404(
        DocumentFlow.objects.prefetch_related("documents__signers"), pk=pk
    )
    return render(request, "documents/flow_detail.html", {"flow": flow})


# ──────────────────────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────────────────────


def _validate_flow_data(
    flow_name,
    doc1_name,
    doc1_pdf_file,
    doc1_signers,
    doc2_name,
    doc2_pdf_file,
    doc2_signers,
):
    errors = []
    if not flow_name:
        errors.append("O nome do fluxo é obrigatório.")
    if not doc1_name:
        errors.append("O nome do Documento 1 é obrigatório.")
    if not doc1_pdf_file:
        errors.append("Selecione o arquivo PDF do Documento 1.")
    elif not doc1_pdf_file.name.lower().endswith(".pdf"):
        errors.append("O arquivo do Documento 1 deve ser um PDF.")
    if not any(n.strip() for n in doc1_signers):
        errors.append("Informe ao menos um signatário para o Documento 1.")
    if not doc2_name:
        errors.append("O nome do Documento 2 é obrigatório.")
    if not doc2_pdf_file:
        errors.append("Selecione o arquivo PDF do Documento 2.")
    elif not doc2_pdf_file.name.lower().endswith(".pdf"):
        errors.append("O arquivo do Documento 2 deve ser um PDF.")
    if not any(n.strip() for n in doc2_signers):
        errors.append("Informe ao menos um signatário para o Documento 2.")
    return errors


def _create_signers(document, names, emails):
    for name, email in zip(names, emails):
        if name.strip():
            Signer.objects.create(
                document=document,
                name=name.strip(),
                email=email.strip(),
            )
