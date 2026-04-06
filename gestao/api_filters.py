import django_filters
from django.db.models import Q
from .models import Material, Ocorrencia


class MaterialFilter(django_filters.FilterSet):
    """
    Filtro avançado para materiais — suporta todos os critérios do painel estatístico.
    Todos os filtros são interligados com data.
    """
    # ---------- DATAS ----------
    data_inicio = django_filters.DateFilter(field_name="data_criacao", lookup_expr='gte')
    data_fim = django_filters.DateFilter(field_name="data_criacao", lookup_expr='lte')
    data_bou_inicio = django_filters.DateFilter(
        field_name="noticiado__ocorrencia__data_registro_bou", lookup_expr='gte'
    )
    data_bou_fim = django_filters.DateFilter(
        field_name="noticiado__ocorrencia__data_registro_bou", lookup_expr='lte'
    )
    ano = django_filters.NumberFilter(field_name="data_criacao", lookup_expr='year')
    mes = django_filters.NumberFilter(field_name="data_criacao", lookup_expr='month')
    semestre = django_filters.NumberFilter(method='filter_semestre')

    # ---------- CATEGORIA / SUBSTÂNCIA ----------
    categoria = django_filters.CharFilter(field_name="categoria")
    substancia = django_filters.CharFilter(field_name="substancia")

    # ---------- STATUS / LOCALIZAÇÃO ----------
    status = django_filters.CharFilter(field_name="status")
    localizacao = django_filters.CharFilter(
        field_name="localizacao_no_cofre", lookup_expr='icontains'
    )

    # ---------- JUDICIAL ----------
    vara = django_filters.CharFilter(field_name="noticiado__ocorrencia__vara")
    processo = django_filters.CharFilter(
        field_name="noticiado__ocorrencia__processo", lookup_expr='icontains'
    )

    # ---------- OCORRÊNCIA ----------
    bou = django_filters.CharFilter(
        field_name="noticiado__ocorrencia__bou", lookup_expr='icontains'
    )
    natureza_penal = django_filters.CharFilter(
        field_name="noticiado__ocorrencia__natureza_penal", lookup_expr='icontains'
    )

    # ---------- NOTICIADO (Autor/Réu) ----------
    autor = django_filters.CharFilter(
        field_name="noticiado__nome", lookup_expr='icontains'
    )

    # ---------- LOTE ----------
    lote = django_filters.NumberFilter(field_name="lote")

    # ---------- BUSCA LIVRE ----------
    palavra_chave = django_filters.CharFilter(method='filter_palavra_chave')

    # ---------- UNIDADE PM ----------
    unidade_origem = django_filters.CharFilter(
        field_name="noticiado__ocorrencia__unidade_origem"
    )

    class Meta:
        model = Material
        fields = []

    def filter_semestre(self, queryset, name, value):
        """Filtra por semestre (1 = Jan-Jun, 2 = Jul-Dez)"""
        if value == 1:
            return queryset.filter(data_criacao__month__gte=1, data_criacao__month__lte=6)
        elif value == 2:
            return queryset.filter(data_criacao__month__gte=7, data_criacao__month__lte=12)
        return queryset

    def filter_palavra_chave(self, queryset, name, value):
        """Busca abrangente em múltiplos campos"""
        if not value:
            return queryset
        return queryset.filter(
            Q(noticiado__ocorrencia__bou__icontains=value) |
            Q(noticiado__ocorrencia__processo__icontains=value) |
            Q(noticiado__nome__icontains=value) |
            Q(numero_lacre__icontains=value) |
            Q(descricao_geral__icontains=value) |
            Q(observacao_material__icontains=value) |
            Q(noticiado__ocorrencia__natureza_penal__icontains=value) |
            Q(noticiado__ocorrencia__observacao__icontains=value)
        )


class OcorrenciaFilter(django_filters.FilterSet):
    """Filtro para busca de ocorrências"""
    bou = django_filters.CharFilter(lookup_expr='icontains')
    vara = django_filters.CharFilter()
    processo = django_filters.CharFilter(lookup_expr='icontains')
    natureza_penal = django_filters.CharFilter(lookup_expr='icontains')
    data_inicio = django_filters.DateFilter(field_name="data_registro_bou", lookup_expr='gte')
    data_fim = django_filters.DateFilter(field_name="data_registro_bou", lookup_expr='lte')
    autor = django_filters.CharFilter(
        field_name="noticiados__nome", lookup_expr='icontains'
    )

    class Meta:
        model = Ocorrencia
        fields = []
