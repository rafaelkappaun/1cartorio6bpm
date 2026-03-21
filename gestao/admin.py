from django.contrib import admin
from .models import LoteIncineracao, Material, RegistroHistorico, Ocorrencia, Noticiado

# Registrando Ocorrencia e Noticiado para você conseguir ver no Admin se precisar
@admin.register(Ocorrencia)
class OcorrenciaAdmin(admin.ModelAdmin):
    list_display = ('bou', 'vara', 'processo', 'data_entrada')
    search_fields = ('bou', 'processo')

@admin.register(Noticiado)
class NoticiadoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ocorrencia')
    search_fields = ('nome',)

@admin.register(LoteIncineracao)
class LoteIncineracaoAdmin(admin.ModelAdmin):
    list_display = ('identificador', 'data_criacao', 'status', 'data_incineracao')
    
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
    list_filter = ('status', 'substancia')
    
    def has_change_permission(self, request, obj=None):
        if obj and obj.lote and obj.lote.status == 'INCINERADO':
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        if obj and obj.lote and obj.lote.status == 'INCINERADO':
            return False
        return True

@admin.register(RegistroHistorico)
class RegistroHistoricoAdmin(admin.ModelAdmin):
    # REMOVIDO 'status_anterior' DA LINHA ABAIXO PARA CORRIGIR O ERRO
    list_display = ('material', 'status_novo', 'data_evento', 'usuario') 
    
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False