from enum import StrEnum
from uuid import UUID

from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone

from core.utils.telegram_utils import TelegramTopic, send_telegram_alert
from front.models import Approval, ApprovalComment, ApprovalModeration, Issue, IssueComment, \
    IssueModeration
from registry.models import Church, Website
from registry.models.base_moderation_models import ModerationStatus
from core.services.admin_email_service import send_email_to_admin
from front.utils.web_utils import get_user_user_agent_and_ip, is_staff_user


class FeedbackType(StrEnum):
    GOOD = "good"
    ERROR = "error"
    COMMENT = "comment"


##############
# NEW REPORT #
##############

class NewReportError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(message)


def get_thread_head(website: Website, head_uuid: UUID | str) -> Issue | Approval:
    issue = Issue.objects.filter(uuid=head_uuid, website=website).first()
    if issue:
        return issue

    approval = Approval.objects.filter(uuid=head_uuid, website=website).first()
    if approval:
        return approval

    # Threads are one level deep
    if IssueComment.objects.filter(uuid=head_uuid).exists() \
            or ApprovalComment.objects.filter(uuid=head_uuid).exists():
        raise NewReportError(400, 'Cannot reply to a reply')

    raise NewReportError(404, f'Report {head_uuid} does not exist')


def save_report(request: HttpRequest, website: Website, church: Church | None,
                feedback_type: FeedbackType, comment: str | None,
                main_report_uuid: UUID | str | None
                ) -> Issue | Approval | IssueComment | ApprovalComment:
    head = get_thread_head(website, main_report_uuid) if main_report_uuid else None

    user, user_agent, ip_address_hash = get_user_user_agent_and_ip(request)
    user_fields = {
        'user': user,
        'user_agent': user_agent,
        'ip_address_hash': ip_address_hash,
    }

    if isinstance(head, Approval):
        report = ApprovalComment.objects.create(approval=head, content=comment or '',
                                                **user_fields)
    elif isinstance(head, Issue):
        report = IssueComment.objects.create(issue=head, content=comment or '', **user_fields)
    elif feedback_type == FeedbackType.GOOD:
        report = Approval.objects.create(website=website, church=church, content=comment,
                                         **user_fields)
    else:
        report = Issue.objects.create(website=website, church=church, content=comment or '',
                                      **user_fields)

    if not user:
        add_necessary_moderation(website, head or report, is_comment=head is not None)

        website_url = request.build_absolute_uri(
            reverse('website_view', kwargs={'website_uuid': website.uuid})
        )

        email_body = (f"New report on website {website.name}\n"
                      f"url: {website_url}\n"
                      + (f"church: {church.name}\n" if church else "")
                      + f"feedback_type: {feedback_type}\n\ncomment:\n{comment}")
        subject = f'New report on confessio for {website.name}'
        send_email_to_admin(subject, email_body)
        send_telegram_alert(message=email_body, topic=TelegramTopic.NEW_REPORTS)

    return report


def new_report(request, website: Website) -> str:
    feedback_type_str = request.POST.get('feedback_type')
    comment = request.POST.get('comment')
    main_report_uuid = request.POST.get('main_report_uuid')

    if not feedback_type_str:
        raise NewReportError(400, 'Feedback type is None')

    try:
        feedback_type = FeedbackType(feedback_type_str)
    except ValueError:
        raise NewReportError(400, f'Invalid feedback type: {feedback_type_str}')

    save_report(request, website, None, feedback_type, comment, main_report_uuid)

    if is_staff_user(request) and request.POST.get('mark_solved') and main_report_uuid:
        head = get_thread_head(website, main_report_uuid)
        if isinstance(head, Issue):
            solve_issue(head)

    return 'Merci pour votre retour !'


def add_necessary_moderation(website: Website, head: Issue | Approval, is_comment: bool):
    if isinstance(head, Approval):
        # A thumbs-up with no comment says nothing a moderator could act on
        if not is_comment and not head.content:
            return
        category = ApprovalModeration.Category.NEW_COMMENT if is_comment \
            else ApprovalModeration.Category.NEW_APPROVAL
        moderation_class, thread_field = ApprovalModeration, 'approval'
    else:
        category = IssueModeration.Category.NEW_COMMENT if is_comment \
            else IssueModeration.Category.NEW_ISSUE
        moderation_class, thread_field = IssueModeration, 'issue'

    # One moderation per thread and category: a new comment reopens it
    moderation, created = moderation_class.objects.get_or_create(
        **{thread_field: head},
        category=category,
        defaults={'diocese': website.get_diocese(), 'status': ModerationStatus.TO_VALIDATE},
    )
    if not created and moderation.status != ModerationStatus.TO_VALIDATE:
        moderation.status = ModerationStatus.TO_VALIDATE
        moderation.save()


###############
# SOLVE ISSUE #
###############

# Moderation statuses are set directly: IssueModeration.set_status would write back to the issue

def solve_issue(issue: Issue):
    if issue.solved_at is None:
        issue.solved_at = timezone.now()
        issue.save()

    for moderation in issue.moderations.exclude(status=ModerationStatus.VALIDATED):
        moderation.status = ModerationStatus.VALIDATED
        moderation.save()


def unsolve_issue(issue: Issue):
    if issue.solved_at is not None:
        issue.solved_at = None
        issue.save()

    for moderation in issue.moderations.filter(status=ModerationStatus.VALIDATED):
        moderation.status = ModerationStatus.TO_VALIDATE
        moderation.save()


##################
# COUNT & LABELS #
##################

def get_count_and_label(website: Website):
    # Filtered in Python to reuse the prefetched issues
    issues = website.issues.all()
    # A solved issue means the data is now right
    solved_issue_count = sum(1 for issue in issues if issue.solved_at is not None)

    count_and_label = []
    for count, label, singular_tooltip, plural_tooltip in [
        (len(website.approvals.all()) + solved_issue_count, '👍', 'avis positif', 'avis positifs'),
        (len(issues) - solved_issue_count, '👎', 'erreur signalée', 'erreurs signalées'),
    ]:
        if count:
            count_and_label.append({
                'count': count,
                'label': label,
                'tooltip': singular_tooltip if count <= 1 else plural_tooltip
            })

    return count_and_label
