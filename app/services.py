"""
HTTP client service for external Spring Boot API integration.
"""

import requests
import logging
from typing import List, Optional, Dict, Any
from fastapi import HTTPException

from app.core.config import Config
from app.models import TestEntity, TestEntityCreate, TestEntityUpdate

logger = logging.getLogger(__name__)


class SpringBootApiClient:
    """HTTP client for Spring Boot API calls"""

    def __init__(self):
        self.base_url = Config.SPRING_BOOT_API_BASE_URL
        self.timeout = 30.0

    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to Spring Boot API"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(
                method=method, 
                url=url, 
                json=json_data, 
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Resource not found")
            elif response.status_code >= 400:
                logger.error(
                    f"Spring Boot API error: {response.status_code} - {response.text}"
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"External API error: {response.text}",
                )

            return response.json()

        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling Spring Boot API: {url}")
            raise HTTPException(status_code=504, detail="External service timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error calling Spring Boot API: {e}")
            raise HTTPException(status_code=503, detail="External service unavailable")

    # TestEntity CRUD operations
    async def get_all_entities(self) -> List[TestEntity]:
        """Get all entities from Spring Boot API"""
        data = self._make_request("GET", "/api/entities")
        return [TestEntity.model_validate(item) for item in data]

    async def get_entity_by_id(self, entity_id: int) -> TestEntity:
        """Get entity by ID from Spring Boot API"""
        data = self._make_request("GET", f"/api/entities/{entity_id}")
        return TestEntity.model_validate(data)

    async def create_entity(self, entity: TestEntityCreate) -> TestEntity:
        """Create new entity via Spring Boot API"""
        data = self._make_request(
            "POST", "/api/entities", json_data=entity.model_dump()
        )
        return TestEntity.model_validate(data)

    async def update_entity(
        self, entity_id: int, entity: TestEntityUpdate
    ) -> TestEntity:
        """Update entity via Spring Boot API"""
        data = self._make_request(
            "PUT",
            f"/api/entities/{entity_id}",
            json_data=entity.model_dump(exclude_unset=True),
        )
        return TestEntity.model_validate(data)

    async def delete_entity(self, entity_id: int) -> Dict[str, str]:
        """Delete entity via Spring Boot API"""
        self._make_request("DELETE", f"/api/entities/{entity_id}")
        return {"message": f"Entity {entity_id} deleted successfully"}

    async def search_entities_by_name(self, name: str) -> List[TestEntity]:
        """Search entities by name via Spring Boot API"""
        data = self._make_request(
            "GET", "/api/entities/search", params={"name": name}
        )
        return [TestEntity.model_validate(item) for item in data]

    # Test scenarios
    async def health_check(self) -> Dict[str, Any]:
        """Basic health check via Spring Boot API"""
        return self._make_request("GET", "/api/test/health")

    async def block_thread(self, seconds: int = 30) -> Dict[str, Any]:
        """Block thread via Spring Boot API"""
        return self._make_request(
            "POST", "/api/test/block-thread", params={"seconds": seconds}
        )

    async def hang_thread(self, seconds: int = 90) -> Dict[str, Any]:
        """Hang thread via Spring Boot API"""
        return self._make_request(
            "POST", "/api/test/hang", params={"seconds": seconds}
        )

    async def cpu_intensive_task(self, seconds: int = 10) -> Dict[str, Any]:
        """CPU intensive task via Spring Boot API"""
        return self._make_request(
            "POST", "/api/test/cpu-intensive", params={"seconds": seconds}
        )

    async def get_thread_status(self) -> Dict[str, Any]:
        """Get thread status via Spring Boot API"""
        return self._make_request("GET", "/api/test/thread-status")


# Global instance
spring_boot_client = SpringBootApiClient()
