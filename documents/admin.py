from django.contrib import admin

from .models import DocumentFlow, Signer, ZapSignDocument


class SignerInline(admin.TabularInline):
    model = Signer
    extra = 0
    readonly_fields = ("zapsign_token", "sign_url", "status")


class ZapSignDocumentInline(admin.TabularInline):
    model = ZapSignDocument
    extra = 0
    readonly_fields = ("zapsign_token", "status", "created_at")
    show_change_link = True


@admin.register(DocumentFlow)
class DocumentFlowAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name",)
    inlines = [ZapSignDocumentInline]


@admin.register(ZapSignDocument)
class ZapSignDocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "flow", "order", "status", "zapsign_token", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "zapsign_token")
    readonly_fields = ("zapsign_token", "created_at")
    inlines = [SignerInline]


@admin.register(Signer)
class SignerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "document", "status", "zapsign_token")
    list_filter = ("status",)
    search_fields = ("name", "email", "zapsign_token")
    readonly_fields = ("zapsign_token", "sign_url")
