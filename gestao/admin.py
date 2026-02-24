from django.contrib import admin
from .models import LoteIncineracao, Material, RegistroHistorico

@admin.register(LoteIncineracao)
class LoteIncineracaoAdmin(admin.ModelAdmin):
    list_display = ('identificador', 'data_criacao', 'status', 'data_incineracao')
    
    # Bloqueia a edição no admin se o status for INCINERADO
    def has_change_permission(self, request, obj=None):
        if obj and obj.status == 'INCINERADO':
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status == 'INCINERADO':
            return False
        return True

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('id', 'substancia', 'status', 'lote')
    
    # Bloqueia a edição do item se o lote associado já estiver INCINERADO
    def has_change_permission(self, request, obj=None):
        if obj and obj.lote and obj.lote.status == 'INCINERADO':
            return False
        return True

    # Bloqueia a exclusão do item se o lote associado já estiver INCINERADO
    def has_delete_permission(self, request, obj=None):
        if obj and obj.lote and obj.lote.status == 'INCINERADO':
            return False
        return True

@admin.register(RegistroHistorico)
class RegistroHistoricoAdmin(admin.ModelAdmin):
    list_display = ('material', 'status_anterior', 'status_novo', 'data_evento')
    # Histórico deve ser apenas leitura para garantir a integridade da auditoria
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False