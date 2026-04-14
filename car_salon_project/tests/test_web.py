import asyncio
import tempfile
import unittest
from pathlib import Path

import httpx

from car_salon.bootstrap import service_session
from car_salon.web import create_app


class WebInterfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "web.db"
        self.app = create_app(self.db_path)

        with service_session(self.db_path) as service:
            self.space = service.spaces.add("Hall A", 2)
            self.seller = service.sellers.add("Seller One")
            self.customer = service.clients.add("Client One", "+000", "client@example.com")
            self.car = service.cars.add("VIN-001", "Toyota", "Camry", 2023, 32000.0)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        async def _send() -> httpx.Response:
            transport = httpx.ASGITransport(app=self.app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
                follow_redirects=True,
            ) as client:
                return await client.request(method, url, **kwargs)

        return asyncio.run(_send())

    def test_dashboard_loads(self) -> None:
        response = self.request("GET", "/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Car Salon FastAPI", response.text)
        self.assertIn("Toyota", response.text)
        self.assertIn("Client One", response.text)

    def test_sale_workflow_works_through_web_routes(self) -> None:
        receive_response = self.request("POST", "/cars/receive-stock", data={"car_id": self.car.id})
        self.assertEqual(receive_response.status_code, 200)

        prepare_response = self.request(
            "POST",
            "/cars/prepare",
            data={"car_id": self.car.id, "note": "Предпродажная подготовка"},
        )
        self.assertEqual(prepare_response.status_code, 200)

        sale_response = self.request(
            "POST",
            "/sales/create",
            data={
                "car_id": self.car.id,
                "client_id": self.customer.id,
                "seller_id": self.seller.id,
                "price": "31500",
            },
        )
        self.assertEqual(sale_response.status_code, 200)

        info_response = self.request("GET", f"/api/cars/{self.car.id}")
        payload = info_response.json()

        self.assertEqual(payload["car"]["state"], "SOLD")
        self.assertTrue(
            any(item["content"].startswith("PREP:") for item in payload["documentation"])
        )
        self.assertTrue(
            any(item["content"].startswith("SALE:") for item in payload["documentation"])
        )

    def test_documentation_can_be_added_from_dashboard_form(self) -> None:
        response = self.request(
            "POST",
            "/cars/add-doc",
            data={"car_id": self.car.id, "content": "Комплектация: Premium"},
        )
        self.assertEqual(response.status_code, 200)

        info_response = self.request("GET", f"/api/cars/{self.car.id}")
        payload = info_response.json()

        self.assertTrue(
            any(item["content"] == "Комплектация: Premium" for item in payload["documentation"])
        )


if __name__ == "__main__":
    unittest.main()
