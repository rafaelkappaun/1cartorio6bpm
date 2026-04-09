import logging
from decimal import Decimal
from django.db.models import Sum, Count, F, Value
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import (
    Ocorrencia, Noticiado, Material, LoteIncineracao, RegistroHistorico,
    NaturezaPenal, EquipePM
)

logger = logging.getLogger(__name__)

class RegistroHistoricoSerializer(serializers.ModelSerializer):
    criado_por_nome = serializers.SerializerMethodField()

    class Meta:
        model = RegistroHistorico
        fields = ['id', 'status_na_epoca', 'observacao', 'data_criacao', 'criado_por', 'criado_por_nome']
        read_only_fields = ['criado_por']

    @extend_schema_field(serializers.CharField())
    def get_criado_por_nome(self, obj):
        if obj.criado_por:
            return obj.criado_por.get_full_name() or obj.criado_por.username
        return "Sistema"


class MaterialSerializer(serializers.ModelSerializer):
    historico = RegistroHistoricoSerializer(many=True, read_only=True)
    criado_por_nome = serializers.SerializerMethodField()
    descricao_amigavel = serializers.SerializerMethodField()

    peso_formatado = serializers.SerializerMethodField()
    ocorrencia_id = serializers.SerializerMethodField()
    bou = serializers.SerializerMethodField()
    processo = serializers.SerializerMethodField()
    unidade_origem = serializers.SerializerMethodField()
    lote_identificador = serializers.SerializerMethodField()
    eprotocolo_geral = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Material
        fields = [
            'id', 'noticiado', 'categoria', 'substancia', 'outra_substancia', 'nome_popular',
            'peso_estimado', 'peso_real', 'unidade', 'lote',
            'descricao_geral', 'valor_monetario', 'recibo_forum', 'comprovante_deposito',
            'numero_lacre', 'localizacao_no_cofre', 'status', 'eprotocolo_geral',
            'observacao_material', 'descricao_amigavel', 'peso_formatado', 'historico',
            'ocorrencia_id', 'bou', 'processo', 'unidade_origem', 'lote_identificador',
            'data_criacao', 'ultima_alteracao', 'criado_por_nome'
        ]

        read_only_fields = ['noticiado']
        extra_kwargs = {
            'numero_lacre': {'required': False, 'allow_blank': True, 'allow_null': True},
            'substancia': {'required': False, 'allow_blank': True, 'allow_null': True},
            'nome_popular': {'required': False, 'allow_blank': True, 'allow_null': True},
            'peso_estimado': {'required': False, 'allow_null': True},
            'unidade': {'required': False, 'allow_blank': True},
            'descricao_geral': {'required': False, 'allow_blank': True, 'allow_null': True},
            'valor_monetario': {'required': False, 'allow_null': True},
        }

    @extend_schema_field(serializers.CharField())
    def get_descricao_amigavel(self, obj):
        return obj.descricao_amigavel()

    @extend_schema_field(serializers.CharField())
    def get_peso_formatado(self, obj):
        return obj.peso_formatado()

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_ocorrencia_id(self, obj):
        return obj.noticiado.ocorrencia.id if obj.noticiado else None
        
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_bou(self, obj):
        return obj.noticiado.ocorrencia.bou if obj.noticiado else None
    
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_processo(self, obj):
        return obj.noticiado.ocorrencia.processo if obj.noticiado else None
    
    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_unidade_origem(self, obj):
        if obj.noticiado:
            return {
                'nome': obj.noticiado.ocorrencia.policial_nome,
                'graduacao': obj.noticiado.ocorrencia.policial_graduacao,
                'rg': obj.noticiado.ocorrencia.rg_policial,
                'unidade': obj.noticiado.ocorrencia.unidade_origem,
            }
        return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_lote_identificador(self, obj):
        return obj.lote.identificador if obj.lote else None

    @extend_schema_field(serializers.CharField())
    def get_criado_por_nome(self, obj):
        if obj.criado_por:
            return obj.criado_por.get_full_name() or obj.criado_por.username
        return "Sistema"



class NoticiadoSerializer(serializers.ModelSerializer):
    materiais = MaterialSerializer(many=True, required=False)

    class Meta:
        model = Noticiado
        fields = ['id', 'nome', 'materiais', 'data_criacao', 'depositario_fiel', 'observacao']
        extra_kwargs = {
            'nome': {'required': True},
            'depositario_fiel': {'required': False, 'default': False},
            'observacao': {'required': False, 'allow_blank': True, 'allow_null': True},
        }


class OcorrenciaSerializer(serializers.ModelSerializer):
    noticiados = NoticiadoSerializer(many=True, required=False)
    cartorario_nome = serializers.SerializerMethodField()

    class Meta:
        model = Ocorrencia
        fields = [
            'id', 'bou', 'vara', 'processo', 'policial_nome', 'policial_graduacao', 
            'rg_policial', 'unidade_origem', 'natureza_penal', 'data_registro_bou', 
            'observacao', 'noticiados', 'criado_por', 'cartorario_nome', 'data_criacao'
        ]
        read_only_fields = ['criado_por']
        extra_kwargs = {
            'bou': {'required': True},
            'vara': {'required': True},
            'policial_nome': {'required': False, 'allow_blank': True},
            'policial_graduacao': {'required': False},
            'rg_policial': {'required': False, 'allow_blank': True},
            'unidade_origem': {'required': False},
            'natureza_penal': {'required': False, 'allow_blank': True},
            'processo': {'required': False, 'allow_blank': True},
            'data_registro_bou': {'required': False},
            'observacao': {'required': False, 'allow_blank': True},
        }

    @extend_schema_field(serializers.CharField(allow_blank=True))
    def get_cartorario_nome(self, obj):
        if obj.criado_por:
            return obj.criado_por.get_full_name() or obj.criado_por.username
        return ""

    def create(self, validated_data):
        logger.error(f"[OCORRENCIA CREATE] Dados: {validated_data}")
        noticiados_data = validated_data.pop('noticiados', [])
        
        user = validated_data.pop('criado_por', None)
        if not user and 'request' in self.context:
            req_user = self.context['request'].user
            user = req_user if req_user.is_authenticated else None
            
        ocorrencia = Ocorrencia.objects.create(criado_por=user, **validated_data)

        for noti_data in noticiados_data:
            materiais_data = noti_data.pop('materiais', [])
            noti = Noticiado.objects.create(ocorrencia=ocorrencia, criado_por=user, **noti_data)
            
            for mat_data in materiais_data:
                # Determina status inicial baseado na categoria
                cat = mat_data.get('categoria')
                if cat == 'ENTORPECENTE':
                    status_inicial = 'RECEBIDO'
                elif cat == 'DINHEIRO':
                    status_inicial = 'AGUARDANDO_GUIA'
                else:
                    status_inicial = 'AGUARDANDO_OFICIO'
                
                mat_data['status'] = mat_data.get('status') or status_inicial
                
                material = Material.objects.create(noticiado=noti, criado_por=user, **mat_data)
                
                RegistroHistorico.objects.create(
                    material=material, criado_por=user,
                    status_na_epoca=material.status,
                    observacao="Material registrado na entrada do boletim."
                )

        return ocorrencia

    def update(self, instance, validated_data):
        noticiados_data = validated_data.pop('noticiados', [])
        
        user = validated_data.pop('criado_por', None)
        if not user and 'request' in self.context:
            user = self.context['request'].user
            
        # Atualiza campos da Ocorrencia
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Sync Noticiados
        kept_noticiado_ids = []
        for noti_data in noticiados_data:
            materiais_data = noti_data.pop('materiais', [])
            noti_id = noti_data.get('id')
            
            if noti_id:
                noti = Noticiado.objects.get(id=noti_id, ocorrencia=instance)
                for attr, value in noti_data.items():
                    setattr(noti, attr, value)
                noti.save()
            else:
                noti = Noticiado.objects.create(ocorrencia=instance, criado_por=user, **noti_data)
            
            kept_noticiado_ids.append(noti.id)

            # Sync Materiais dentro do Noticiado
            kept_material_ids = []
            for mat_data in materiais_data:
                mat_id = mat_data.get('id')
                
                # Definir status inicial se for novo
                if not mat_id:
                    cat = mat_data.get('categoria')
                    if cat == 'ENTORPECENTE':
                        status_inicial = 'RECEBIDO'
                    elif cat == 'DINHEIRO':
                        status_inicial = 'AGUARDANDO_GUIA'
                    else:
                        status_inicial = 'AGUARDANDO_OFICIO'
                    mat_data['status'] = mat_data.get('status') or status_inicial

                if mat_id:
                    material = Material.objects.get(id=mat_id, noticiado=noti)
                    status_anterior = material.status
                    for attr, value in mat_data.items():
                        setattr(material, attr, value)
                    material.save()
                    
                    if status_anterior != material.status:
                        RegistroHistorico.objects.create(
                            material=material, criado_por=user,
                            status_na_epoca=material.status,
                            observacao=f"Status alterado manualmente na edição do BO."
                        )
                else:
                    material = Material.objects.create(noticiado=noti, criado_por=user, **mat_data)
                    RegistroHistorico.objects.create(
                        material=material, criado_por=user,
                        status_na_epoca=material.status,
                        observacao="Novo material adicionado via edição do BO."
                    )
                
                kept_material_ids.append(material.id)

            # Deleta materiais removidos desse noticiado
            noti.materiais.exclude(id__in=kept_material_ids).delete()

        # Deleta noticiados removidos
        instance.noticiados.exclude(id__in=kept_noticiado_ids).delete()

        return instance


class LoteIncineracaoSerializer(serializers.ModelSerializer):
    materiais = MaterialSerializer(many=True, read_only=True)
    criado_por_nome = serializers.SerializerMethodField()
    processos_count = serializers.SerializerMethodField()
    peso_total = serializers.SerializerMethodField()
    processos_list = serializers.SerializerMethodField()

    class Meta:
        model = LoteIncineracao
        fields = [
            'id', 'identificador', 'data_incineracao', 'status', 
            'eprotocolo_geral', 'materiais', 'data_criacao', 'criado_por_nome',
            'processos_count', 'peso_total', 'processos_list'
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_processos_count(self, obj):
        if hasattr(obj, '_processos_count_cache'):
            return obj._processos_count_cache
        return obj.materiais.values('noticiado__ocorrencia__bou').distinct().count()

    @extend_schema_field(serializers.FloatField())
    def get_peso_total(self, obj):
        if hasattr(obj, '_peso_total_cache'):
            return obj._peso_total_cache
        try:
            from django.db.models import Sum
            from django.db.models.functions import Coalesce
            result = obj.materiais.aggregate(
                total=Sum(Coalesce('peso_real', 'peso_estimado'))
            )
            return float(result['total'] or 0)
        except Exception:
            return 0.0

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_processos_list(self, obj):
        if hasattr(obj, '_processos_list_cache'):
            return obj._processos_list_cache
        values = obj.materiais.values_list(
            'noticiado__ocorrencia__processo', 
            'noticiado__ocorrencia__bou'
        ).distinct()
        procs = []
        seen = set()
        for processo, bou in values:
            key = processo or bou
            if key and key not in seen:
                procs.append(key)
                seen.add(key)
        return procs

    @extend_schema_field(serializers.CharField())
    def get_criado_por_nome(self, obj):
        if obj.criado_por:
            return obj.criado_por.get_full_name() or obj.criado_por.username
        return "Sistema"



class NaturezaPenalSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturezaPenal
        fields = ['id', 'nome', 'tipo']


class EquipePMSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipePM
        fields = ['id', 'nome', 'graduacao', 'rg', 'unidade']
