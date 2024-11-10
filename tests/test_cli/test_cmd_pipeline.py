""" Test cid pipeline command
"""
import json
import os
import pytest
from click.testing import CliRunner
from cli import (__main__, cmd_pipeline)
from pydantic import ValidationError
from unittest import TestCase
from unittest.mock import MagicMock, patch
from util.model import (ValidationResult, PipelineConfig)
from util.common_utils import get_logger

# TODO - pipeline_run integration test cases
# file and pipeline_name
# override error handling
# validation error handling
# dry_run branch handling
# local flag handling

def test_cid():
    """ Test the main cid command just by calling it with --help option
    """
    runner = CliRunner()
    result = runner.invoke(__main__.cid, '--help')
    # 0 exit code mean successful
    assert result.exit_code == 0


def test_pipeline_help():
    """ Test the main pipeline command just by calling it with --help option
    """
    runner = CliRunner()
    result = runner.invoke(cmd_pipeline.pipeline, '--help')
    # 0 exit code mean successful
    assert result.exit_code == 0

class TestPipelineRun(TestCase):
    """ Test class to perform integration test between the cli cmd 
    cid pipeline run and corresponding controller method of 
    run_pipeline(). The downstream method will be patched whenever 
    necessary

    Args:
        TestCase (class): base class
    """
    def setUp(self):
        self.runner = CliRunner()
        
        self.fail_validation = ValidationResult(valid=False, error_msg="", pipeline_config={})
        self.logger = get_logger("tests.test_cli.test_cmd_pipeline.TestPipelineRun")
        
        # Load sample validation result from json file
        validation_result_path = os.path.join(os.path.dirname(__file__),'sample_validation_res.json')
        with open(validation_result_path, 'r', encoding='utf-8') as openfile:
            # Reading from json file
            validation_result_dict = json.load(openfile)
        self.success_validation_res = ValidationResult.model_validate(validation_result_dict)
        pipeline_config_dict = self.success_validation_res.pipeline_config
        self.success_validation_res.pipeline_config = PipelineConfig.model_validate(pipeline_config_dict)
        self.mock_pipeline_config = pipeline_config_dict
        #self.logger.debug(self.success_validation_res)
        
    # Test input check logics
    def test_both_pipeline_name_file_path(self):
        """test if --file and --pipeline are passed as arguments. it should return error
        as it can't be both.
        """
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run', '--pipeline', 'valid_pipeline_default',
                                                    '--file', '.cicd-pipelines/pipelines.yml'])
        # Common exit code for invalid argument is 2
        assert result.exit_code == 2
        assert result.output.rstrip() == "cid: invalid flag. you can only pass --file or --pipeline and can't be both."
    
    def test_invalid_override(self):
        """ test if error correctly caught when invalid override value is passed on
        """
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run', '--override', 'no_value_key'])
        assert result.exit_code == 2
    
    @patch("controller.controller.YamlParser.parse_yaml_by_pipeline_name", side_effect=FileNotFoundError())
    def test_fail_yaml_parsing_from_pipeline_name(self, mock_parse):
        """ test the case when attempting to parse pipeline config based on pipeline_name but fail
        
        Args:
            mock_parse (MagicMock): mock the parse_yaml_by_pipeline_name function
        """
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run', '--pipeline', 'no_value_key'])
        assert result.exit_code == 1
    
    @patch("controller.controller.YamlParser.parse_yaml_file", side_effect=FileNotFoundError())
    def test_fail_yaml_parsing_from_file_path(self, mock_parse):
        """ test the case when attempting to parse pipeline config based on file_path but fail
        
        Args:
            mock_parse (MagicMock): mock the parse_yaml_file function
        """
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run'])
        assert result.exit_code == 1
    
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.YamlParser.parse_yaml_file")
    def test_fail_validation(self, mock_parse, mock_validate):
        """ Test the case where the run_pipeline execution reach the validation stage
        but fail

        Args:
            mock_validate (MagicMock): mock the validate_config function
            mock_parse (MagicMock): mock the parse_yaml_file function
        """
        mock_parse.return_value = self.mock_pipeline_config
        mock_validate.return_value = self.fail_validation
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run'])
        assert result.exit_code == 1
            
    @patch("controller.controller.Controller.dry_run")
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.YamlParser.parse_yaml_file")
    def test_fail_dry_run(self, mock_parse, mock_validate, mock_dry_run):
        """ Test the case where the run_pipeline execution reach the dry run stage
        but fail

        Args:
            mock_validate (MagicMock): mock the validate_config method
            mock_parse (MagicMock): mock the parse_yaml_file method
            mock_dry_run(MagicMock): mock the dry_run method 
        """
        mock_parse.return_value = self.mock_pipeline_config
        mock_validate.return_value = self.success_validation_res
        mock_dry_run.return_value = (False, "")
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run', '--dry-run'])
        assert result.exit_code == 1
    
    @patch("controller.controller.Controller.dry_run")
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.YamlParser.parse_yaml_file")
    def test_success_dry_run_with_mock(self, mock_parse, mock_validate, mock_dry_run):
        """ Test the case where the run_pipeline execution reach the dry_run
        and success

        Args:
            mock_validate (MagicMock): mock the validate_config method
            mock_parse (MagicMock): mock the parse_yaml_file method
            mock_dry_run(MagicMock): mock the dry_run method 
        """
        mock_parse.return_value = self.mock_pipeline_config
        mock_validate.return_value = self.success_validation_res
        mock_dry_run.return_value = (True, "")
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run', '--dry-run'])
        assert result.exit_code == 0
    
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.YamlParser.parse_yaml_file")
    def test_success_integrated_dry_run(self, mock_parse, mock_validate):
        """ Test the case where the run_pipeline execution reach the dry_run
        and success, with integration test on dry run util class

        Args:
            mock_validate (MagicMock): mock the validate_config method
            mock_parse (MagicMock): mock the parse_yaml_file method
        """
        mock_parse.return_value = self.mock_pipeline_config
        mock_validate.return_value = self.success_validation_res
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run', '--dry-run','--yaml'])
        assert result.exit_code == 0

    @patch("controller.controller.Controller._actual_pipeline_run")
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.YamlParser.parse_yaml_file")
    def test_success_actual_run(self, mock_parse, mock_validate, mock_actual_run):
        """ Test the case where the run_pipeline execution reach the 
        actual run and success

        Args:
            mock_validate (MagicMock): mock the validate_config method
            mock_parse (MagicMock): mock the parse_yaml_file method
            mock_dry_run(MagicMock): mock the dry_run method 
        """
        mock_parse.return_value = self.mock_pipeline_config
        mock_validate.return_value = self.success_validation_res
        mock_actual_run.return_value = (True, "")
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run'])
        assert result.exit_code == 0

    @patch("controller.controller.Controller._actual_pipeline_run")
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.YamlParser.parse_yaml_file")
    def test_fail_actual_run(self, mock_parse, mock_validate, mock_actual_run):
        """ Test the case where the run_pipeline execution reach the 
        actual run and fail

        Args:
            mock_validate (MagicMock): mock the validate_config method
            mock_parse (MagicMock): mock the parse_yaml_file method
            mock_dry_run(MagicMock): mock the dry_run method 
        """
        mock_parse.return_value = self.mock_pipeline_config
        mock_validate.return_value = self.success_validation_res
        mock_actual_run.return_value = (False, "")
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run'])
        assert result.exit_code == 1
        
        mock_actual_run.side_effect = ValidationError.from_exception_data("",[])
        result = self.runner.invoke(cmd_pipeline.pipeline, ['run'])
        assert result.exit_code == 1
    
    # Integration test
    @patch("controller.controller.Controller._actual_pipeline_run")
    @patch("controller.controller.ConfigChecker.validate_config")
    @patch("controller.controller.YamlParser.parse_yaml_file")
    def test_success_actual_run_with_override(self, mock_parse, mock_validate, mock_actual_run):
        """ Test the case where the run_pipeline execution reach the 
        actual run and success, with overrides apply

        Args:
            mock_validate (MagicMock): mock the validate_config method
            mock_parse (MagicMock): mock the parse_yaml_file method
            mock_dry_run(MagicMock): mock the dry_run method 
        """
        mock_parse.return_value = self.mock_pipeline_config
        mock_validate.return_value = self.success_validation_res
        mock_actual_run.return_value = (True, "")
        cmd_list = ['run', '--override', 'global.docker.image=gradle:jdk8']
        result = self.runner.invoke(cmd_pipeline.pipeline, cmd_list)
        assert result.exit_code == 0
        
def test_pipeline_log():
    """call pipeline log
    """
    runner = CliRunner()
    result = runner.invoke(cmd_pipeline.pipeline, ['log'])

    assert result.exit_code == 0
