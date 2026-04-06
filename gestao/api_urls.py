from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import OcorrenciaViewSet, NoticiadoViewSet, MaterialViewSet, LoteIncineracaoViewSet, NaturezaPenalViewSet, EquipePMViewSet

router = DefaultRouter()
router.register(r'ocorrencias', OcorrenciaViewSet)
router.register(r'noticiados', NoticiadoViewSet)
router.register(r'materiais', MaterialViewSet)
router.register(r'lotes', LoteIncineracaoViewSet)
router.register(r'naturezas-penais', NaturezaPenalViewSet)
router.register(r'equipe-pm', EquipePMViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
