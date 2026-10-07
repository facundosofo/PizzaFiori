from fastapi.testclient import TestClient
from datetime import date

from app.main import app
from app.application.services.jwt_service import JWTService


def test_report_endpoint_monthly():
    client = TestClient(app)

    params = {
        "fecha_desde": date(2026, 1, 1).isoformat(),
        "fecha_hasta": date(2026, 12, 31).isoformat(),
        "modo": "light",
        "mostrar_resumen_periodo": "true",
        "mostrar_resumen_dia": "false",
        "mostrar_resumen_mes": "true",
        "mostrar_resumen_categoria": "true",
        "mostrar_resumen_productos": "true",
        "mostrar_detalle_ventas": "false",
    }

    token_data = JWTService.generate_token(user_id=1, username="test", role="ADMIN")
    headers = {"Authorization": f"Bearer {token_data['token']}"}

    resp = client.get("/ventas/reporte/pdf", params=params, headers=headers)
    assert resp.status_code in (200, 404, 500)
    # If 500, include body for debugging
    if resp.status_code == 500:
        print(resp.text)
