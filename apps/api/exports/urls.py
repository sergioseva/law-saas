from django.urls import path

from .views import (
    ExcelExportView,
    ExportDownloadView,
    ExportStatusView,
    PdfExportView,
)

app_name = "exports"

urlpatterns = [
    path("excel", ExcelExportView.as_view(), name="excel"),
    path("pdf", PdfExportView.as_view(), name="pdf"),
    path("<str:task_id>", ExportStatusView.as_view(), name="status"),
    path("<str:task_id>/download", ExportDownloadView.as_view(), name="download"),
]
