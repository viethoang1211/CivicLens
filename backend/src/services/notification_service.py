import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.citizen import Citizen
from src.models.notification import Notification
from src.models.submission import Submission


async def create_notification(
    db: AsyncSession,
    citizen_id: uuid.UUID,
    submission_id: uuid.UUID | None,
    notification_type: str,
    title: str,
    body: str,
) -> Notification:
    notification = Notification(
        citizen_id=citizen_id,
        submission_id=submission_id,
        type=notification_type,
        title=title,
        body=body,
        sent_at=datetime.now(timezone.utc),
    )
    db.add(notification)
    await db.flush()

    # Push via Alibaba Cloud EMAS
    citizen_result = await db.execute(select(Citizen).where(Citizen.id == citizen_id))
    citizen = citizen_result.scalar_one_or_none()
    if citizen and citizen.push_token:
        await _send_push(citizen.push_token, title, body)

    return notification


async def notify_step_advanced(
    db: AsyncSession, submission: Submission, department_name: str, step_order: int
) -> None:
    await create_notification(
        db=db,
        citizen_id=submission.citizen_id,
        submission_id=submission.id,
        notification_type="step_advanced",
        title=f"Hồ sơ đã chuyển sang {department_name}",
        body=f"Hồ sơ của bạn đã hoàn thành bước {step_order - 1} và chuyển sang {department_name}.",
    )


async def notify_info_requested(
    db: AsyncSession, submission: Submission, message: str
) -> None:
    await create_notification(
        db=db,
        citizen_id=submission.citizen_id,
        submission_id=submission.id,
        notification_type="info_requested",
        title="Cần bổ sung hồ sơ",
        body=message,
    )


async def notify_completed(db: AsyncSession, submission: Submission) -> None:
    await create_notification(
        db=db,
        citizen_id=submission.citizen_id,
        submission_id=submission.id,
        notification_type="completed",
        title="Hồ sơ đã hoàn thành",
        body="Hồ sơ của bạn đã được xử lý xong.",
    )


async def notify_delayed(db: AsyncSession, submission: Submission, department_name: str) -> None:
    await create_notification(
        db=db,
        citizen_id=submission.citizen_id,
        submission_id=submission.id,
        notification_type="delayed",
        title=f"Hồ sơ bị chậm tại {department_name}",
        body=f"Hồ sơ của bạn đang chậm tiến độ tại {department_name}.",
    )


async def _send_push(push_token: str, title: str, body: str) -> None:
    """Send push notification via Alibaba Cloud EMAS.

    Placeholder — real implementation calls EMAS Push API.
    """
    pass
