from home.management.abstract_command import AbstractCommand
from registry.models import Church
from home.utils.hash_utils import hash_string_to_hex
from sourcing.services.church_llm_name_service import get_prompt_template_for_name


class Command(AbstractCommand):
    help = "One shot command to fill church name with llm name."

    def handle(self, *args, **options):
        self.info('Starting one shot command to fill church name with llm name...')
        counter = 0
        for church in Church.objects.all():
            prompt_template = get_prompt_template_for_name()
            prompt_template_hash = hash_string_to_hex(prompt_template)
            church_llm_name = church.llm_names\
                .filter(prompt_template_hash=prompt_template_hash).first()
            if church_llm_name:
                if church.name != church_llm_name.new_name:
                    # self.info(f'Updating church {church.uuid} ({church.name}) '
                    #           f'with LLM name {church_llm_name.new_name}.')
                    church.name = church_llm_name.new_name
                    church.save()
                else:
                    self.info(f'Church {church.uuid} ({church.name}) already has the LLM name, '
                              f'skipping update.')
            else:
                self.warning(f'No LLM name found for church {church.uuid} ({church.name}), '
                             f'skipping update.')
        self.success(f'Successfully filled {counter} church names with LLM names.')
