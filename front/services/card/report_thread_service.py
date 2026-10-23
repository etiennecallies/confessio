from dataclasses import dataclass
from uuid import UUID

from attaching.models import FileNote, FileNoteComment, FileNoteModeration
from front.models import Approval, ApprovalComment, ApprovalModeration, Issue, IssueComment, \
    IssueModeration
from registry.models import Website
from registry.models.base_moderation_models import ModerationMixin


@dataclass
class ReportThread:
    head: Issue | Approval | FileNote
    comments: list[IssueComment | ApprovalComment | FileNoteComment]

    @property
    def is_approval(self) -> bool:
        return isinstance(self.head, Approval)

    @property
    def is_issue(self) -> bool:
        return isinstance(self.head, Issue)

    @property
    def is_file_note(self) -> bool:
        return isinstance(self.head, FileNote)


def get_report_threads(website: Website) -> list[ReportThread]:
    heads = list(Issue.objects.filter(website=website).prefetch_related('comments__user')) \
        + list(Approval.objects.filter(website=website).prefetch_related('comments__user')) \
        + list(FileNote.objects.filter(website=website).prefetch_related('comments__user'))
    heads.sort(key=lambda head: head.created_at, reverse=True)

    return [ReportThread(head=head,
                         comments=sorted(head.comments.all(), key=lambda c: c.created_at))
            for head in heads]


def get_moderations_by_thread_uuid(threads: list[ReportThread]
                                   ) -> dict[UUID, list[ModerationMixin]]:
    head_uuids = [thread.head.uuid for thread in threads]

    moderations_by_thread_uuid = {}
    for moderation in IssueModeration.objects.filter(issue_id__in=head_uuids):
        moderations_by_thread_uuid.setdefault(moderation.issue_id, []).append(moderation)
    for moderation in ApprovalModeration.objects.filter(approval_id__in=head_uuids):
        moderations_by_thread_uuid.setdefault(moderation.approval_id, []).append(moderation)
    for moderation in FileNoteModeration.objects.filter(file_note_id__in=head_uuids):
        moderations_by_thread_uuid.setdefault(moderation.file_note_id, []).append(moderation)

    return moderations_by_thread_uuid
