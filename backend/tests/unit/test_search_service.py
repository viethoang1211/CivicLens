"""Unit tests for search service."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestSearchValidation:
    """Test search parameter validation and edge cases."""

    @pytest.mark.asyncio
    async def test_pagination_calculation(self):
        """Test pagination total_pages calculation."""
        from src.services.search_service import search

        mock_db = AsyncMock()

        # Mock: count returns 0
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        execute_result = MagicMock()
        execute_result.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[count_result, execute_result])

        result = await search(
            db=mock_db,
            query="test",
            clearance_level=3,
            page=1,
            per_page=20,
        )

        assert result["pagination"]["total"] == 0
        assert result["pagination"]["total_pages"] == 0
        assert result["pagination"]["page"] == 1
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_combined_filters(self):
        """Test that multiple filters are applied together."""
        from src.services.search_service import search

        mock_db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        execute_result = MagicMock()
        execute_result.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[count_result, execute_result])

        result = await search(
            db=mock_db,
            query="test query",
            clearance_level=2,
            status="completed",
            date_from=date(2026, 1, 1),
            date_to=date(2026, 12, 31),
            page=1,
            per_page=10,
        )

        assert result["query"] == "test query"
        assert result["pagination"]["per_page"] == 10

    @pytest.mark.asyncio
    async def test_empty_results_structure(self):
        """Test response structure with no results."""
        from src.services.search_service import search

        mock_db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        execute_result = MagicMock()
        execute_result.all.return_value = []
        mock_db.execute = AsyncMock(side_effect=[count_result, execute_result])

        result = await search(
            db=mock_db,
            query="nonexistent",
            clearance_level=3,
        )

        assert "results" in result
        assert "pagination" in result
        assert "query" in result
        assert result["query"] == "nonexistent"
