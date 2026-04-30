from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import DocumentFlow, Signer, ZapSignDocument
from .services import create_zapsign_document

# ──────────────────────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────────────────────


def _get_folders():
    return (
        DocumentFlow.objects.values_list("folder", flat=True)
        .distinct()
        .order_by("folder")
    )


def _get_subfolders():
    return (
        DocumentFlow.objects.values_list("name", flat=True).distinct().order_by("name")
    )


def _validate_flow_data(
    flow_name,
    folder_name,
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
    if not folder_name:
        errors.append("Selecione ou informe uma pasta.")
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


# ──────────────────────────────────────────────────────────────
# Views
# ──────────────────────────────────────────────────────────────


@login_required
def index(request):
    """Lista todos os fluxos de documentos com filtros."""
    flows = DocumentFlow.objects.prefetch_related("documents__signers").order_by(
        "-created_at"
    )

    status_filter = request.GET.get("status", "")
    search = request.GET.get("q", "").strip()
    folder_filter = request.GET.get("folder", "")

    if status_filter:
        flows = flows.filter(status=status_filter)
    if search:
        flows = flows.filter(name__icontains=search)
    if folder_filter:
        flows = flows.filter(folder=folder_filter)

    return render(
        request,
        "documents/index.html",
        {
            "flows": flows,
            "status_filter": status_filter,
            "search": search,
            "folder_filter": folder_filter,
            "folders": _get_folders(),
            "total": DocumentFlow.objects.count(),
        },
    )


@login_required
def create_flow(request):
    """Formulário para criar um novo fluxo com 2 documentos encadeados."""
    ctx_base = {"folders": _get_folders(), "subfolders": _get_subfolders()}

    if request.method == "POST":
        flow_name = request.POST.get("flow_name", "").strip()
        folder_name = request.POST.get("folder_name", "").strip() or "Sistema_RN"

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
            folder_name,
            doc1_name,
            doc1_pdf_file,
            doc1_signer_names,
            doc2_name,
            doc2_pdf_file,
            doc2_signer_names,
        )

        if errors:
            return render(
                request,
                "documents/create_flow.html",
                {"post_data": request.POST, **ctx_base},
            )

        flow = DocumentFlow.objects.create(name=flow_name, folder=folder_name)

        doc1 = ZapSignDocument.objects.create(
            flow=flow, order=1, name=doc1_name, pdf_file=doc1_pdf_file
        )
        _create_signers(doc1, doc1_signer_names, doc1_signer_emails)

        doc2 = ZapSignDocument.objects.create(
            flow=flow, order=2, name=doc2_name, pdf_file=doc2_pdf_file
        )
        _create_signers(doc2, doc2_signer_names, doc2_signer_emails)

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
                request,
                "documents/create_flow.html",
                {"post_data": request.POST, **ctx_base},
            )

        return redirect("documents:flow_detail", pk=flow.pk)

    return render(request, "documents/create_flow.html", ctx_base)


@login_required
def flow_detail(request, pk):
    """Detalha um fluxo com seus documentos e links de assinatura."""
    flow = get_object_or_404(
        DocumentFlow.objects.prefetch_related("documents__signers"), pk=pk
    )
    return render(request, "documents/flow_detail.html", {"flow": flow})
