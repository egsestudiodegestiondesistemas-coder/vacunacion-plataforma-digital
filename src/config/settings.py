from dataclasses import dataclass

@dataclass(frozen=True)
class AppSettings:
    app_name: str = "VACUNACION Plataforma Digital"
    developer_name: str = "EGS | Estudio de Gestión de Sistemas"
    initial_city: str = "San Francisco"
    initial_province: str = "Córdoba"
    country: str = "Argentina"
    content_status: str = "BORRADOR — NO PUBLICAR"
    medical_notice: str = "Información general. No reemplaza la consulta profesional ni la revisión del carnet."

SETTINGS = AppSettings()
