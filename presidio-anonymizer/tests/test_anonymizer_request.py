from typing import List


import pytest

from presidio_anonymizer.anonymizers import Replace, Mask
from presidio_anonymizer.entities.anonymizer_request import AnonymizerRequest
from presidio_anonymizer.entities.invalid_exception import InvalidParamException


@pytest.mark.parametrize(
    # fmt: off
    "request_json, result_text",
    [
        ({}, "Invalid input, text can not be empty",),
        ({
             "text": "hello world, my name is Jane Doe. My number is: 034453334",
             "analyzer_results": [
                 {
                     "start": 28,
                     "end": 32,
                     "score": 0.8,
                     "entity_type": "NUMBER"
                 }
             ],
             "anonymizers": {
                 "default": {
                     "type": "none"
                 }
             }
         }, "Invalid anonymizer class 'none'.",),
        ({
             "text": "hello world, my name is Jane Doe. My number is: 034453334",
             "analyzer_results": [
                 {
                     "end": 32,
                     "score": 0.8,
                 }
             ]
         }, "Invalid input, analyzer result must contain start",),
        ({
             "text": "hello world, my name is Jane Doe. My number is: 034453334",
         }, "Invalid input, analyzer results can not be empty",),
        ({
             "analyzer_results": [
                 {
                     "start": 28,
                     "end": 32,
                     "score": 0.8,
                     "entity_type": "NUMBER"
                 }
             ]
         }, "Invalid input, text can not be empty",)
    ],
    # fmt: on
)
def test_given_invalid_json_then_request_creation_should_fail(
        request_json, result_text
):
    with pytest.raises(InvalidParamException) as e:
        AnonymizerRequest(request_json)
    assert result_text == e.value.err_msg


def test_given_valid_json_then_request_creation_should_succeed():
    content = get_content()
    data = AnonymizerRequest(content)
    assert len(data._anonymizers_config) == 2
    phone_number_anonymizer = data.get_anonymizers_config().get("PHONE_NUMBER")
    assert phone_number_anonymizer.params == {
        "masking_char": "*",
        "chars_to_mask": 4,
        "from_end": True,
    }
    assert phone_number_anonymizer.anonymizer_class == Mask
    default_anonymizer = data.get_anonymizers_config().get("DEFAULT")
    assert default_anonymizer.params == {"new_value": "ANONYMIZED"}
    assert default_anonymizer.anonymizer_class == Replace
    assert len(data._analysis_results) == len(content.get("analyzer_results"))
    assert data._analysis_results == data.get_analysis_results()
    for result_a in data._analysis_results:
        same_result_in_content = __find_element(
            content.get("analyzer_results"), result_a.entity_type
        )
        assert same_result_in_content
        assert result_a.score == same_result_in_content.get("score")
        assert result_a.start == same_result_in_content.get("start")
        assert result_a.end == same_result_in_content.get("end")


@pytest.mark.parametrize(
    # fmt: off
    "original_text,start,end",
    [
        ("hello world", 5, 12),
        ("hello world", 12, 16),
    ],
    # fmt: on
)
def test_given_analyzer_result_with_an_incorrect_text_positions_then_we_fail(
        original_text, start, end):
    content = {
        "text": original_text,
        "analyzer_results": [
            {"start": start, "end": end, "score": 0.8, "entity_type": "NAME"},
        ],
    }
    content.get("analyzer_results")
    err_msg = f"Invalid analyzer result, start: {start} and end: " \
              f"{end}, while text length is only 11."
    with pytest.raises(InvalidParamException, match=err_msg):
        AnonymizerRequest(content)


@pytest.mark.parametrize(
    # fmt: off
    "original_text,start,end",
    [
        ("hello world", 5, 12),
        ("hello world", 12, 16),
    ],
    # fmt: on
)
def test_given_analyzer_result_with_an_incorrect_text_positions_then_we_fail_(
        original_text, start, end):
    content = {
        "text": original_text,
        "analyzer_results": [
            {"start": start, "end": end, "score": 0.8, "entity_type": "NAME"},
        ],
    }
    content.get("analyzer_results")
    err_msg = f"Invalid analyzer result, start: {start} and end: " \
              f"{end}, while text length is only 11."
    with pytest.raises(InvalidParamException, match=err_msg):
        AnonymizerRequest(content)


def __find_element(content: List, entity_type: str):
    for result in content:
        if result.get("entity_type") == entity_type:
            return result
    return None


def get_content():
    return {
        "text": "hello world, my name is Jane Doe. My number is: 034453334",
        "anonymizers": {
            "DEFAULT": {"type": "replace", "new_value": "ANONYMIZED"},
            "PHONE_NUMBER": {
                "type": "mask",
                "masking_char": "*",
                "chars_to_mask": 4,
                "from_end": True,
            },
        },
        "analyzer_results": [
            {"start": 24, "end": 32, "score": 0.8, "entity_type": "NAME"},
            {"start": 24, "end": 28, "score": 0.8, "entity_type": "FIRST_NAME"},
            {"start": 29, "end": 32, "score": 0.6, "entity_type": "LAST_NAME"},
            {"start": 48, "end": 57, "score": 0.95, "entity_type": "PHONE_NUMBER"},
        ],
    }
