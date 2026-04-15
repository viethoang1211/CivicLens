import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.models.notification import Notification
from src.security.auth import CitizenIdentity, get_current_citizen

router = APIRouter()


@router.get("")
async def list_notifications(
    is_read: bool | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    citizen: CitizenIdentity = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    query = select(Notification).where(Notification.citizen_id == citizen.citizen_id)
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    unread_q = select(func.count()).where(
        Notification.citizen_id == citizen.citizen_id, Notification.is_read.is_(False)
    )
    unread_count = (await db.execute(unread_q)).scalar() or 0

    query = query.order_by(Notification.sent_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    notifications = result.scalars().all()

    return {
        "items": [
            {
                "id": str(n.id),
                "submission_id": str(n.submission_id) if n.submission_id else None,
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "is_read": n.is_read,
                "sent_at": n.sent_at.isoformat(),
            }
            for n in notifications
        ],
        "total": total,
        "unread_count": unread_count,
        "page": page,
    }


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: uuid.UUID,
    citizen: CitizenIdentity = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.citizen_id == citizen.citizen_id
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    notification.read_at = datetime.now(UTC)
    await db.commit()

    return {"id": str(notification.id), "is_read": True, "read_at": notification.read_at.isoformat()}
