from home.models import Parsing, ParsingModeration
from scheduling.public import init_schedulings_for_parsing


################
# EDIT PARSING #
################

def set_human_json(parsing: Parsing, some_json: dict, json_version: str):
    needs_reschedule = False
    if parsing.human_json:
        if parsing.human_json != some_json:
            needs_reschedule = True
    else:
        if parsing.llm_json != some_json:
            needs_reschedule = True
    parsing.human_json = some_json
    parsing.human_json_version = json_version
    parsing.save()
    if needs_reschedule:
        init_schedulings_for_parsing(parsing)


#########################
# MODERATION VALIDATION #
#########################

class ParsingValidationError(Exception):
    pass


def on_parsing_human_validation(parsing_moderation: ParsingModeration):
    parsing = parsing_moderation.parsing
    if parsing.human_json is None:
        if parsing.llm_json is None:
            raise ParsingValidationError(
                'No human nor LLM json for parsing, can not be validated'
            )

        set_llm_json_as_human_json(parsing)


def set_llm_json_as_human_json(parsing: Parsing):
    set_human_json(parsing, parsing.llm_json, parsing.llm_json_version)
