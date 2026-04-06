from django.contrib import admin
from django.utils.html import format_html
from .models import LoteIncineracao, Material, RegistroHistorico, Ocorrencia, Noticiado

@admin.register(Ocorrencia)
class OcorrenciaAdmin(admin.ModelAdmin):
    list_display = ('bou', 'vara', 'processo', 'data_criacao')
    search_fields = ('bou', 'processo')
    list_filter = ('vara', 'data_criacao')
    date_hierarchy = 'data_criacao'

@admin.register(Noticiado)
class NoticiadoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'get_bou')
    search_fields = ('nome', 'ocorrencia__bou')

    def get_bou(self, obj):
        return obj.ocorrencia.bou
    get_bou.short_description = 'BOU Origem'

@admin.register(LoteIncineracao)
class LoteIncineracaoAdmin(admin.ModelAdmin):
    list_display = ('identificador', 'data_criacao', 'status_colorido', 'get_total_itens', 'data_incineracao')
    list_filter = ('status',)
    
    def status_colorido(self, obj):
        colors = {
            'INCINERADO': 'red',
            'ABERTO': 'green',
            'FECHADO': 'orange',
        }
        return format_html(
            '<b style="color: {};">{}</b>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_colorido.short_description = 'Status'

    def get_total_itens(self, obj):
        return obj.materiais.count()
    get_total_itens.short_description = 'Qtd Itens'

    # Travas de segurança para dados incinerados
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
    list_display = ('get_bou', 'categoria', 'substancia', 'status', 'lote_link')
    list_filter = ('categoria', 'status', 'substancia', 'noticiado__ocorrencia__vara')
    search_fields = ('noticiado__ocorrencia__bou', 'noticiado__nome', 'numero_lacre')
    
    def get_bou(self, obj):
        return obj.noticiado.ocorrencia.bou
    get_bou.short_description = 'BOU'

    def lote_link(self, obj):
        if obj.lote:
            return obj.lote.identificador
        return "-"
    lote_link.short_description = 'Lote'

    # Bloqueio de edição para material já destruído
    def has_change_permission(self, request, obj=None):
        if obj and obj.lote and obj.lote.status == 'INCINERADO':
            return False
        return True

@admin.register(RegistroHistorico)
class RegistroHistoricoAdmin(admin.ModelAdmin):
    list_display = ('data_criacao', 'material', 'status_na_epoca', 'criado_por') 
    list_filter = ('status_na_epoca', 'criado_por', 'data_criacao')
    readonly_fields = ('data_criacao', 'criado_por', 'status_na_epoca', 'material')
    
    # Histórico nunca deve ser apagado ou editado manualmente
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False