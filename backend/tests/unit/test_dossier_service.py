"""Unit tests for dossier_service.check_completeness OR-logic."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_dossier_with_snapshot():
    """Dossier with requirement_snapshot for OR-logic testing."""
    dossier = MagicMock()
    dossier.id = uuid.uuid4()
    dossier.case_type_id = uuid.uuid4()
    slot_a = str(uuid.uuid4())
    slot_b = str(uuid.uuid4())
    slot_c = str(uuid.uuid4())
    dossier.requirement_snapshot = {
        "groups": [
            {
                "id": str(uuid.uuid4()),
                "label": "Giấy khai sinh",
                "is_mandatory": True,
                "slots": [
                    {"id": slot_a, "label": "Bản gốc"},
                    {"id": slot_b, "label": "Bản công chứng"},
                ],
            },
            {
                "id": str(uuid.uuid4()),
                "label": "Ảnh hộ chiếu (tùy chọn)",
                "is_mandatory": False,
                "slots": [
                    {"id": slot_c, "label": "Ảnh 4x6"},
                ],
            },
        ],
    }
    return dossier, slot_a, slot_b, slot_c


class TestCheckCompletenessOrLogic:
    """Test OR-logic: fulfilling any one slot in a mandatory group satisfies it."""

    @pytest.mark.asyncio
    async def test_one_slot_fulfilled_in_mandatory_group_is_complete(self, mock_dossier_with_snapshot):
        dossier, slot_a, slot_b, slot_c = mock_dossier_with_snapshot
        db = AsyncMock()

        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = dossier

        # Only slot_a is fulfilled (one of two in mandatory group)
        docs_result = MagicMock()
        docs_result.all.return_value = [(uuid.UUID(slot_a),)]

        db.execute.side_effect = [dossier_result, docs_result]

        from src.services.dossier_service import check_completeness
        result = await check_completeness(dossier.id, db)

        assert result["complete"] is True
        assert result["missing_groups"] == []

    @pytest.mark.asyncio
    async def test_no_slots_fulfilled_in_mandatory_group_is_incomplete(self, mock_dossier_with_snapshot):
        dossier, slot_a, slot_b, slot_c = mock_dossier_with_snapshot
        db = AsyncMock()

        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = dossier

        # No slots fulfilled
        docs_result = MagicMock()
        docs_result.all.return_value = []

        db.execute.side_effect = [dossier_result, docs_result]

        from src.services.dossier_service import check_completeness
        result = await check_completeness(dossier.id, db)

        assert result["complete"] is False
        assert len(result["missing_groups"]) == 1
        assert result["missing_groups"][0]["label"] == "Giấy khai sinh"

    @pytest.mark.asyncio
    async def test_optional_group_unfulfilled_still_complete(self, mock_dossier_with_snapshot):
        dossier, slot_a, slot_b, slot_c = mock_dossier_with_snapshot
        db = AsyncMock()

        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = dossier

        # Mandatory group fulfilled (slot_b), optional group NOT fulfilled
        docs_result = MagicMock()
        docs_result.all.return_value = [(uuid.UUID(slot_b),)]

        db.execute.side_effect = [dossier_result, docs_result]

        from src.services.dossier_service import check_completeness
        result = await check_completeness(dossier.id, db)

        assert result["complete"] is True

    @pytest.mark.asyncio
    async def test_all_mandatory_groups_fulfilled(self, mock_dossier_with_snapshot):
        dossier, slot_a, slot_b, slot_c = mock_dossier_with_snapshot
        # Add another mandatory group
        extra_slot = str(uuid.uuid4())
        dossier.requirement_snapshot["groups"].append({
            "id": str(uuid.uuid4()),
            "label": "CCCD",
            "is_mandatory": True,
            "slots": [{"id": extra_slot, "label": "CCCD bản gốc"}],
        })
        db = AsyncMock()

        dossier_result = MagicMock()
        dossier_result.scalar_one_or_none.return_value = dossier

        # Both mandatory groups fulfilled
        docs_result = MagicMock()
        docs_result.all.return_value = [
            (uuid.UUID(slot_a),),
            (uuid.UUID(extra_slot),),
        ]

        db.execute.side_effect = [dossier_result, docs_result]

        from src.services.dossier_service import check_completeness
        result = await check_completeness(dossier.id, db)

        assert result["complete"] is True
