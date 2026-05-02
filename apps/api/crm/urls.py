from rest_framework.routers import DefaultRouter

from .views import ActionViewSet, ClientViewSet, DocumentViewSet

app_name = "crm"

router = DefaultRouter(trailing_slash=False)
router.register("clients", ClientViewSet, basename="client")
router.register("actions", ActionViewSet, basename="action")
router.register("documents", DocumentViewSet, basename="document")

urlpatterns = router.urls
