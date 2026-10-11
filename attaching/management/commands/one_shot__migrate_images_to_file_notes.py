from collections import Counter

from django.db import transaction

from attaching.models import FileNote, FileNoteModeration, Image, ImageModeration
from attaching.services.file_note_mirror_service import get_file_note_fields, \
    get_file_note_moderation_fields
from core.management.abstract_command import AbstractCommand

ImagePruning = Image.prunings.through
FileNotePruning = FileNote.prunings.through


class Command(AbstractCommand):
    help = "Backfill FileNote/FileNoteModeration from the images predating double write."

    def handle(self, *args, **options):
        with transaction.atomic():
            file_notes = self.migrate_file_notes()
            self.migrate_prunings(file_notes)
            self.migrate_moderations()
        self.check_counts()

    def migrate_file_notes(self) -> list[FileNote]:
        mirrored_uuids = set(FileNote.objects.values_list('uuid', flat=True))
        images = Image.objects.exclude(uuid__in=mirrored_uuids)
        file_notes = [FileNote(uuid=image.uuid, created_at=image.created_at,
                               updated_at=image.updated_at, **get_file_note_fields(image))
                      for image in images]

        self.info(f'{len(mirrored_uuids)} images already mirrored')
        self.bulk_create_keeping_timestamps(FileNote, file_notes)
        return file_notes

    def migrate_prunings(self, file_notes: list[FileNote]):
        image_prunings = ImagePruning.objects\
            .filter(image_id__in=[file_note.uuid for file_note in file_notes])
        file_note_prunings = [FileNotePruning(filenote_id=image_pruning.image_id,
                                              pruning_id=image_pruning.pruning_id)
                              for image_pruning in image_prunings]
        FileNotePruning.objects.bulk_create(file_note_prunings, batch_size=1000,
                                            ignore_conflicts=True)
        self.success(f'Created {len(file_note_prunings)} file note prunings')

    def migrate_moderations(self):
        mirrored_uuids = set(FileNoteModeration.objects.values_list('uuid', flat=True))
        image_moderations = ImageModeration.objects.exclude(uuid__in=mirrored_uuids)
        file_note_moderations = [
            FileNoteModeration(uuid=moderation.uuid, created_at=moderation.created_at,
                               updated_at=moderation.updated_at,
                               **get_file_note_moderation_fields(moderation))
            for moderation in image_moderations
        ]

        self.info(f'{len(mirrored_uuids)} image moderations already mirrored')
        self.bulk_create_keeping_timestamps(FileNoteModeration, file_note_moderations)
        status_counts = Counter(moderation.status for moderation in file_note_moderations)
        self.info(f'FileNoteModeration statuses: {dict(status_counts)}')

    def bulk_create_keeping_timestamps(self, model, objs):
        timestamps = {obj.uuid: (obj.created_at, obj.updated_at) for obj in objs}
        # auto_now_add and auto_now override timestamps on create, but bulk_update skips pre_save
        model.objects.bulk_create(objs, batch_size=1000)
        for obj in objs:
            obj.created_at, obj.updated_at = timestamps[obj.uuid]
        model.objects.bulk_update(objs, ['created_at', 'updated_at'], batch_size=1000)
        self.success(f'Created {len(objs)} {model.__name__}')

    def check_counts(self):
        self.log_count_check('images', Image.objects.count(),
                             FileNote.objects.filter(uuid__in=Image.objects.values('uuid'))
                             .count())
        self.log_count_check('image moderations', ImageModeration.objects.count(),
                             FileNoteModeration.objects
                             .filter(uuid__in=ImageModeration.objects.values('uuid')).count())

        image_links = set(ImagePruning.objects.values_list('image_id', 'pruning_id'))
        file_note_links = set(FileNotePruning.objects.values_list('filenote_id', 'pruning_id'))
        self.log_count_check('image prunings', len(image_links),
                             len(image_links & file_note_links))

    def log_count_check(self, label, images_count, mirrored_count):
        if images_count == mirrored_count:
            self.success(f'All {images_count} {label} are mirrored')
        else:
            self.warning(f'{mirrored_count} {label} mirrored out of {images_count}')
