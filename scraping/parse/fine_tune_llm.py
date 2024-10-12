import json
import time
from datetime import datetime
from typing import Optional

from scraping.parse.llm_client import get_openai_client
from scraping.parse.parse_with_llm import build_input_messages, get_prompt_template
from scraping.parse.schedules import SchedulesList


###############
# Local jsonl #
###############

def save_jsonl(jsonl_filepath, messages_list):
    with open(jsonl_filepath, 'w') as jsonl_file:
        for entry in messages_list:
            jsonl_file.write(json.dumps(entry) + '\n')


def get_json_file_name_and_path(dataset_name):
    jsonl_filename = f'{dataset_name}.jsonl'
    jsonl_filepath = f'/tmp/{jsonl_filename}'
    return jsonl_filename, jsonl_filepath


def build_jsonl_file(dataset: list[tuple[str, dict[int, str], int, SchedulesList]]):
    dataset_name = f'parsings_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    jsonl_filename, jsonl_filepath = get_json_file_name_and_path(dataset_name)

    prompt_template = get_prompt_template()

    # Build messages list
    messages_list = []
    for truncated_html, church_desc_by_id, year, schedules_list in dataset:
        input_messages = build_input_messages(
            prompt_template,
            truncated_html,
            church_desc_by_id,
            year
        )
        output_message = {
            "role": "assistant",
            "content": schedules_list.model_dump_json()
        }
        messages = {
            "messages": input_messages + [output_message]
        }
        messages_list.append(messages)

    # Create and write to a JSONL file
    save_jsonl(jsonl_filepath, messages_list)

    return dataset_name


###############
# OpenAI file #
###############

def upload_file_on_openai(dataset_name):
    client = get_openai_client()
    jsonl_filename, jsonl_filepath = get_json_file_name_and_path(dataset_name)

    file = client.files.create(
        file=open(jsonl_filepath, "rb"),
        purpose="fine-tune"
    )

    return file


###############
# Fine-tuning #
###############

def launch_fine_tuning_job(file, base_model: str) -> Optional[str]:
    client = get_openai_client()

    client.fine_tuning.jobs.create(
        training_file=file.id,
        model=base_model
    )

    # List all fine-tune jobs
    fine_tune_jobs = client.fine_tuning.jobs.list()

    # Optionally, get the most recent fine-tune job ID
    if fine_tune_jobs.data:
        latest_fine_tune_job = fine_tune_jobs.data[0]
        fine_tune_job_id = latest_fine_tune_job.id
        print(f"Latest Fine-tune Job ID: {fine_tune_job_id}")
    else:
        print("No fine-tune jobs found.")
        return

    return fine_tune_job_id


def check_fine_tuning_job_completion(fine_tune_job_id) -> tuple[Optional[str], Optional[str]]:
    client = get_openai_client()

    print("Checking if fine-tuning has completed...")
    fine_tune_job = client.fine_tuning.jobs.retrieve(fine_tune_job_id)
    if fine_tune_job.fine_tuned_model is None:
        if fine_tune_job.estimated_finish:
            remaining_seconds = fine_tune_job.estimated_finish - time.time()
            print(f'status: {fine_tune_job.status}, remaining time: {remaining_seconds} seconds')
        else:
            print(f'status: {fine_tune_job.status}, finished_at: {fine_tune_job.finished_at}')

        return None, None
    elif fine_tune_job.status == 'failed':
        print(fine_tune_job)
        print("Fine-tuning failed.")
        # TODO extract error message
        return None, str(fine_tune_job)

    print("Fine-tuning completed.")
    return fine_tune_job.fine_tuned_model, None
