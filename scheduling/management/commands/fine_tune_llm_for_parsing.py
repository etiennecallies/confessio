from core.management.abstract_command import AbstractCommand
from scheduling.models.parsing_models import FineTunedLLM
from scraping.services.fine_tune_llm_service import build_parsing_moderation_dataset, train_llm, \
    watch_fine_tuning_job_completion


class Command(AbstractCommand):
    help = "Launch the fine-tuning of LLM for parsing"

    def add_arguments(self, parser):
        parser.add_argument('-w', '--watch', help='watch for completed fine-tuning job',
                            action='store_true')

    def handle(self, *args, **options):
        if options['watch']:
            self.info(f'Watching for completed fine-tuning job...')
            running_fine_tune_llms = FineTunedLLM.objects.filter(
                status=FineTunedLLM.Status.FINE_TUNING
            ).all()
            self.info(f'Found {len(running_fine_tune_llms)} running fine-tuning jobs')
            for running_fine_tune_llm in running_fine_tune_llms:
                fine_tuned_llm = watch_fine_tuning_job_completion(running_fine_tune_llm)
                if fine_tuned_llm.status == FineTunedLLM.Status.DRAFT:
                    self.success(
                        f'Successfully fine-tuned llm with name {fine_tuned_llm.fine_tuned_model}')
                    self.warning(f'WARNING: Fine-tuned model is still in draft status. '
                                 f'You shall set it to prod in admin interface.')
                elif fine_tuned_llm.status == FineTunedLLM.Status.FAILED:
                    self.error(
                        f'Fine-tuned llm with job_id {fine_tuned_llm.fine_tune_job_id} failed')
                else:
                    self.warning(
                        f'Fine-tuned llm with job_id {fine_tuned_llm.fine_tune_job_id} '
                        f'is still in {fine_tuned_llm.status} status')
            return

        self.info(f'Building sentence dataset...')
        parsing_moderation_dataset = build_parsing_moderation_dataset()
        self.info(f'Got {len(parsing_moderation_dataset)} validated parsings')
        self.info(f'Training LLM ...')
        fine_tuned_llm = train_llm(parsing_moderation_dataset)
        self.success(f'Successfully fine-tuned llm with status {fine_tuned_llm.status}')
