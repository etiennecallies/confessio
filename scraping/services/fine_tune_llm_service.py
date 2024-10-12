from home.models import ParsingModeration, FineTunedLLM
from home.utils.date_utils import get_current_year
from scraping.parse.fine_tune_llm import build_jsonl_file, upload_file_on_openai, \
    launch_fine_tuning_job, check_fine_tuning_job_completion
from scraping.parse.schedules import SchedulesList
from scraping.services.parse_pruning_service import get_truncated_html

LLM_MIN_ITEMS_FOR_TRAIN = 15


def build_parsing_moderation_dataset() -> list[ParsingModeration]:
    return ParsingModeration.objects.filter(validated_at__isnull=False).all()


def train_llm(parsing_moderation_dataset: list[ParsingModeration]) -> FineTunedLLM:
    if len(parsing_moderation_dataset) < LLM_MIN_ITEMS_FOR_TRAIN:
        raise ValueError(f"Not enough parsings in dataset to train llm, "
                         f"{len(parsing_moderation_dataset)} out of {LLM_MIN_ITEMS_FOR_TRAIN}")

    # TODO split dataset into test and train

    dataset = []
    for parsing_moderation in parsing_moderation_dataset:
        # TODO get the truncated_html from parsing
        truncated_html = get_truncated_html(parsing_moderation.parsing.pruning)
        church_desc_by_id = parsing_moderation.parsing.church_desc_by_id
        # TODO get the current_year from parsing
        current_year = get_current_year()
        schedules_list = SchedulesList(**parsing_moderation.validated_schedules_list)

        dataset.append((
            truncated_html,
            church_desc_by_id,
            current_year,
            schedules_list
        ))

    dataset_name = build_jsonl_file(dataset)
    openai_file = upload_file_on_openai(dataset_name)
    base_model = "gpt-4o-2024-08-06"

    fine_tune_job_id = launch_fine_tuning_job(openai_file, base_model)
    if fine_tune_job_id is None:
        raise ValueError("Fine tuning job failed")

    fine_tuned_llm = FineTunedLLM(
        status=FineTunedLLM.Status.FINE_TUNING,
        dataset_name=dataset_name,
        base_model=base_model,
        fine_tuned_model=fine_tune_job_id,
    )
    fine_tuned_llm.save()
    fine_tuned_llm.parsing_moderations.set(parsing_moderation_dataset)

    watch_fine_tuning_job_completion(fine_tuned_llm)

    return fine_tuned_llm


def watch_fine_tuning_job_completion(fine_tuned_llm: FineTunedLLM) -> FineTunedLLM:
    fine_tuned_model, error_detail = check_fine_tuning_job_completion(
        fine_tuned_llm.fine_tune_job_id)
    if fine_tuned_model:
        fine_tuned_llm.status = FineTunedLLM.Status.DRAFT
        fine_tuned_llm.fine_tuned_model = fine_tuned_model
        fine_tuned_llm.save()
        return fine_tuned_llm

    if error_detail:
        fine_tuned_llm.status = FineTunedLLM.Status.FAILED
        fine_tuned_llm.error_detail = error_detail
        fine_tuned_llm.save()
        return fine_tuned_llm
