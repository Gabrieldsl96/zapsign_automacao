from django.db import models


class DocumentFlow(models.Model):
    """Representa um fluxo de 2 documentos encadeados."""

    STATUS_CHOICES = [
        ("doc1_pending", "Documento 1 Aguardando Assinatura"),
        ("doc2_pending", "Documento 2 Aguardando Assinatura"),
        ("completed", "Concluído"),
    ]

    name = models.CharField(max_length=255, verbose_name="Nome do Fluxo")
    folder = models.CharField(
        max_length=255, verbose_name="Pasta ZapSign", default="Sistema_RN"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="doc1_pending",
        verbose_name="Status",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Fluxo de Documentos"
        verbose_name_plural = "Fluxos de Documentos"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ZapSignDocument(models.Model):
    """Representa um documento individual dentro de um fluxo."""

    STATUS_CHOICES = [
        ("not_created", "Não Enviado"),
        ("pending", "Aguardando Assinatura"),
        ("signed", "Assinado"),
    ]

    flow = models.ForeignKey(
        DocumentFlow,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Fluxo",
    )
    order = models.IntegerField(verbose_name="Ordem")
    name = models.CharField(max_length=255, verbose_name="Nome do Documento")
    pdf_file = models.FileField(
        upload_to="pdfs/",
        verbose_name="Arquivo PDF",
        null=True,
        blank=True,
    )
    zapsign_token = models.CharField(
        max_length=255, blank=True, verbose_name="Token ZapSign"
    )
    signed_file_url = models.URLField(
        blank=True, verbose_name="Link do Documento Assinado"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="not_created",
        verbose_name="Status",
    )
    created_at = models.DateTimeField(null=True, blank=True, verbose_name="Enviado em")

    class Meta:
        verbose_name = "Documento ZapSign"
        verbose_name_plural = "Documentos ZapSign"
        ordering = ["order"]

    def __str__(self):
        return f"{self.flow.name} — Documento {self.order}: {self.name}"


class Signer(models.Model):
    """Representa um signatário de um documento."""

    STATUS_CHOICES = [
        ("new", "Novo"),
        ("pending", "Pendente"),
        ("signed", "Assinado"),
    ]

    document = models.ForeignKey(
        ZapSignDocument,
        on_delete=models.CASCADE,
        related_name="signers",
        verbose_name="Documento",
    )
    name = models.CharField(max_length=255, verbose_name="Nome")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    zapsign_token = models.CharField(
        max_length=255, blank=True, verbose_name="Token ZapSign"
    )
    sign_url = models.URLField(blank=True, verbose_name="Link de Assinatura")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
        verbose_name="Status",
    )

    class Meta:
        verbose_name = "Signatário"
        verbose_name_plural = "Signatários"

    def __str__(self):
        return f"{self.name} ({self.document.name})"
