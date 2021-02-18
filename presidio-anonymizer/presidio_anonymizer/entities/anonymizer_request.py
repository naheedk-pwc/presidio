"""
Engine request entity.

It get the data and validate it before the engine receives it.
"""
import logging

from presidio_anonymizer.entities import AnalyzerResult
from presidio_anonymizer.entities import AnalyzerResults
from presidio_anonymizer.entities import InvalidParamException


class AnonymizerRequest:
    """Input validation for the anonymize process."""

    logger = logging.getLogger("presidio-anonymizer")

    def __init__(self, data: dict, anonymizers):
        """Handle and validate data for the text replacement.

        :param data: a map which contains the anonymizers, analyzer_results and text
        """
        self.anonymizers = anonymizers
        self._anonymizers = {}
        self._analysis_results = AnalyzerResults()
        self.__validate_and_insert_input(data)
        self.default_anonymizer = {
            "type": "replace",
            "anonymizer": self.anonymizers["replace"],
        }

    def get_anonymizer_dto(self, entity_type: str):
        """
        Get the right anonymizer_dto from the list.

        When anonymizer_dto does not exist, we fall back to default.
        :param analyzer_result: the result we are going to do the anonymization on
        :return: anonymizer_dto
        """
        anonymizer_dto = self._anonymizers.get(entity_type)
        if not anonymizer_dto:
            anonymizer_dto = self._anonymizers.get("DEFAULT")
            if not anonymizer_dto:
                anonymizer_dto = self.default_anonymizer
        anonymizer_dto["entity_type"] = entity_type
        return anonymizer_dto

    def get_text(self):
        """Get the text we are working on."""
        return self._text

    def get_analysis_results(self):
        """Get the analysis results."""
        return self._analysis_results

    def __validate_and_insert_input(self, data: dict):
        self.__handle_text(data)
        self.__handle_analyzer_results(data)
        self.__handle_anonymizers(data)

    def __handle_analyzer_results(self, data):
        """
        Go over analyzer results, check they are valid and convert to AnalyzeResult.

        :param data: contains the text, anonymizers and analyzer_results
        :return: None
        """
        analyzer_results = data.get("analyzer_results")
        if not analyzer_results:
            self.logger.debug("invalid input, json missing field: analyzer_results")
            raise InvalidParamException(
                "Invalid input, " "analyzer results can not be empty"
            )
        text_len = len(data.get("text"))
        for analyzer_result in analyzer_results:
            analyzer_result = AnalyzerResult(analyzer_result)
            analyzer_result.validate_position_in_text(text_len)
            self._analysis_results.append(analyzer_result)

    def __handle_anonymizers(self, data):
        """
        Go over the anonymizers and get the relevant anonymizer class for it.

        Inserts the class to the anonymizer so the engine will use it.
        :param data: contains the text, anonymizers and analyzer_results
        :return: None
        """
        anonymizers = data.get("anonymizers")
        if anonymizers is not None:
            for key, anonymizer_dto in anonymizers.items():
                self.logger.debug(f"converting {anonymizer_dto} to anonymizer class")
                anonymizer = self.__get_anonymizer(anonymizer_dto)
                self.logger.debug(f"applying class {anonymizer} to {anonymizer_dto}")
                anonymizer_dto["anonymizer"] = anonymizer
                self._anonymizers[key] = anonymizer_dto

    def __handle_text(self, data):
        self._text = data.get("text")
        if not self._text:
            self.logger.debug("invalid input, json is missing text field")
            raise InvalidParamException("Invalid input, text can not be empty")

    def __get_anonymizer(self, anonymizer):
        """
        Extract the anonymizer class from the anonymizers list.

        :param anonymizer: a single anonymizer value
        :return: Anonymizer
        """
        anonymizer_type = anonymizer.get("type").lower()
        anonymizer = self.anonymizers.get(anonymizer_type)
        if not anonymizer:
            self.logger.error(f"No such anonymizer class {anonymizer_type}")
            raise InvalidParamException(
                f"Invalid anonymizer class '{anonymizer_type}'."
            )
        return anonymizer
