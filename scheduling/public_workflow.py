from scheduling.workflows.pruning.action_interfaces import DummyActionInterface
from scheduling.workflows.pruning.extract.extract_content import ExtractV1Interface
from scheduling.workflows.pruning.extract.extract_interface import BaseExtractInterface, ExtractMode


######################
# EXTRACT CONTENT V1 #
######################

def extract_refined_content(refined_content: str, extract_interface: BaseExtractInterface = None
                            ) -> list[str] | None:
    if extract_interface is None:
        extract_interface = ExtractV1Interface(DummyActionInterface())

    paragraphs_lines_and_indices = extract_interface.extract_paragraphs_lines_and_indices(
        refined_content, ExtractMode.EXTRACT)
    if not paragraphs_lines_and_indices:
        return None

    extracted_html_list = []
    for paragraph_lines, paragraph_indices in paragraphs_lines_and_indices:
        extracted_html_list.append('<br>\n'.join(paragraph_lines))

    return extracted_html_list
