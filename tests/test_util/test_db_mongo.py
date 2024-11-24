""" All testing method for db_mongo 
"""
import copy
import mongomock
import pprint
import pytest
from pymongo import (errors)
import unittest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from collections import OrderedDict
import util.constant as c
from util.db_mongo import MongoAdapter
from util.common_utils import get_logger
from util.model import (PipelineInfo, RepoConfig, SessionDetail)
logger = get_logger("tests.test_util.test_db_mongo")
MONGO_DB_NAME = "CICDControllerDB"
MONGO_PIPELINES_TABLE = "repo_configs"
MONGO_JOBS_TABLE = "jobs_history"
MONGO_REPOS_TABLE = "sessions"

class TestMongoDB(unittest.TestCase):
    
    _mock_mongo = mongomock.MongoClient()
    
    def setUp(self):
        self.session_data = SessionDetail(
            user_id="random",
            repo_name="random_repo",
            repo_url="random_url",
            branch="main",
            commit_hash="abcdef",
            is_remote=True,
        )
        self.repo_config_data = RepoConfig(
            repo_name="random_repo",
            repo_url="random_url",
            branch="main"
        )
        self.pipeline_config = {
            'global':{
                c.KEY_PIPE_NAME: "test_pipeline",
                c.KEY_DOCKER:{
                        c.KEY_DOCKER_REG: 'dockerhub',
                        c.KEY_DOCKER_IMG: 'image'
                    },
                c.KEY_ARTIFACT_PATH: "/temp"
            },
            'stages':{
                'stage1':{
                    "job_graph": {
                        "checkout": [
                            "compile"
                        ],
                        "compile": []
                    },
                    "job_groups": [
                        [
                            "checkout",
                            "compile"
                        ]
                    ]
                }
            },
            'jobs':{
                'job1': {
                c.JOB_SUBKEY_STAGE: 'stage',
                c.JOB_SUBKEY_ALLOW: True,
                c.JOB_SUBKEY_NEEDS: [],
                c.KEY_DOCKER:{
                    c.KEY_DOCKER_REG: 'dockerhub',
                    c.KEY_DOCKER_IMG: 'image'
                },
                c.KEY_ARTIFACT_PATH: 'path',
                c.JOB_SUBKEY_SCRIPTS:['sh','ls'],
                }
            }
        }
        self.pipeline_info = {
            "pipeline_name": "test_pipeline",
            "pipeline_file_name": "test_pipeline.yml",
            "pipeline_config":self.pipeline_config
        }
    
    @patch("util.db_mongo.MongoClient", return_value=_mock_mongo)
    def test_pipeline_crud(self, mock_client):
        """ test crud operation with pipeline

        Args:
            mock_client (mongomock.MongoClient): mock mongo_db
        """
        mongo_adapter = MongoAdapter()
        # Test insert new repo_config_data
        status = mongo_adapter.insert_repo_pipelines(
            self.repo_config_data)
        assert status == True

    @patch("util.db_mongo.MongoClient", return_value=_mock_mongo)
    def test_job_crud(self, mock_client):
        """ Test CRUD operation with job
        Args:
            mock_client (mongomock.MongoClient): mock mongo_db
        """
        mongo_adapter = MongoAdapter()
        job_log = {
            'pipeline_name': 'test_pipeline',
            'job_run': 1,
            'job_log': {}
        }
        

        # Test insert and get
        pipeline_history = {
            "pipeline_name": "sample_pipeline",
            "pipeline_file_name": "sample_pipeline.yml",
            "last_commit_hash": "random",
            "pipeline_config":self.pipeline_config
        }
        his_object = PipelineInfo.model_validate(pipeline_history)
        result_id = mongo_adapter.insert_job(
            his_object, self.pipeline_config)
        search_result = mongo_adapter.get_job(result_id)
        assert search_result['pipeline_config_used'] == self.pipeline_config

        # Test update
        updated_history = copy.deepcopy(search_result)
        updated_history['success'] = True
        mongo_adapter.update_job(result_id, updated_history)
        new_search_result = mongo_adapter.get_job(result_id)
        assert new_search_result == updated_history

    

    @patch("util.db_mongo.MongoAdapter._delete", side_effect=errors.PyMongoError())
    @patch("util.db_mongo.MongoAdapter._update", side_effect=errors.PyMongoError())
    @patch("util.db_mongo.MongoAdapter._retrieve", side_effect=errors.PyMongoError())
    @patch("util.db_mongo.MongoAdapter._insert", side_effect=errors.PyMongoError())
    @patch("util.db_mongo.MongoClient", return_value=_mock_mongo)
    def test_job_crud_exception(self, mock_client, insert, get, update, delete):
        """ Test exception catching of crud operation with job

        Args:
            mock_client (mongomock.MongoClient): mock mongo_db
            insert (MagicMock): mock insert method
            get (MagicMock): mock get method
            update (MagicMock): mock update method
            delete (MagicMock): mock delete method
        """
        mongo_adapter = MongoAdapter()
        job_log = {
            'pipeline_name': 'test_pipeline',
            'job_run': 1,
            'job_log': {}
        }
        pipeline_history = {
            "pipeline_name": "sample_pipeline",
            "pipeline_file_name": "sample_pipeline.yml",
            "last_commit_hash": "random",
            "pipeline_config":self.pipeline_config
        }
        his_object = PipelineInfo.model_validate(pipeline_history)
        result_id = mongo_adapter.insert_job(
            his_object, self.pipeline_config)
        assert result_id is None
        search_result = mongo_adapter.get_job("")
        assert search_result == {}
        update_result = mongo_adapter.update_job(job_log, self.pipeline_config)
        assert update_result == False
        pass
    
    @patch("util.db_mongo.MongoClient", return_value=_mock_mongo)
    def test_update_with_query(self, mock_client):
        """ Test update and retrieve by query method

        Args:
            mock_client (mongomock.MongoClient): mock mongo_db
        """
        mongo_adapter = MongoAdapter()
        # First try update a data which doesnot exist for the query
        query_data = {
            'user_id':self.session_data.user_id
        }
        updated_data = self.session_data.model_dump()
        update_status = mongo_adapter._update_by_query(
            query_data, updated_data, MONGO_DB_NAME, MONGO_REPOS_TABLE)
        assert update_status == True
        retrieved_data = mongo_adapter._retrieve_by_query(
            query_data, MONGO_DB_NAME, MONGO_REPOS_TABLE
        )
        retrieved_data.pop('_id')
        assert retrieved_data == updated_data
        logger.debug(retrieved_data)
        # Now try update the previous data
        updated_data['repo_name'] = 'random_repo2'
        update_status = mongo_adapter._update_by_query(
            query_data, updated_data, MONGO_DB_NAME, MONGO_REPOS_TABLE)
        assert update_status == True
        retrieved_data = mongo_adapter._retrieve_by_query(
            query_data, MONGO_DB_NAME, MONGO_REPOS_TABLE
        )
        retrieved_data.pop('_id')
        assert retrieved_data == updated_data

    @patch("util.db_mongo.MongoClient", return_value=_mock_mongo)
    def test_update_pipeline_config(self, mock_client):
        """Test updating pipeline config with success, failure, and exception cases."""
        mongo_adapter = MongoAdapter()

        # Success case
        # Test new insert
        result = mongo_adapter.update_pipeline_info(
            repo_name="test_repo",
            repo_url="https://github.com/test/test_repo",
            branch="main",
            pipeline_name="test_pipeline",
            updates=self.pipeline_info
        )
        assert result is True
        
        # Test modification
        pipeline_config = copy.deepcopy(self.pipeline_config)
        pipeline_config[c.KEY_GLOBAL][c.KEY_ARTIFACT_PATH] = "new_temp"
        result = mongo_adapter.update_pipeline_info(
            repo_name="test_repo",
            repo_url="https://github.com/test/test_repo",
            branch="main",
            pipeline_name="test_pipeline",
            updates={"pipeline_config":pipeline_config}
        )
        
        assert result is True
        query_filter = {
            "repo_name":"test_repo",
            "repo_url":"https://github.com/test/test_repo",
            "branch":"main"
        }
        stored_data = mongo_adapter._retrieve_by_query(
            query_filter, MONGO_DB_NAME, MONGO_PIPELINES_TABLE
        )
        logger.debug(pprint.pformat(stored_data))

        # Exception case
        mock_client.side_effect = errors.PyMongoError("Database error")
        result = mongo_adapter.update_pipeline_info(
            repo_name="test_repo",
            repo_url="https://github.com/test/test_repo",
            branch="main",
            pipeline_name="test_pipeline",
            updates={"pipeline_config":pipeline_config}
        )
        assert result is False
