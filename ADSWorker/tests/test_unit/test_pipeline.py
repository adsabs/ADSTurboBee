import sys
import os

import unittest
import json
import re
import os
import math
import httpretty
import mock
from io import BytesIO
from mock import patch

from ADSWorker.tests import test_base
from ADSWorker import matcher, app, updater, importer
from ADSWorker.models import AuthorInfo, ClaimsLog, Records, Base
from ADSWorker.pipeline import workers

class TestWorkers(test_base.TestUnit):
    """
    Tests the GenericWorker's methods
    """
    
    def create_app(self):
        app.init_app({
            'SQLALCHEMY_URL': 'sqlite:///',
            'SQLALCHEMY_ECHO': False
        })
        Base.metadata.bind = app.session.get_bind()
        Base.metadata.create_all()
        return app
    
    def tearDown(self):
        test_base.TestUnit.tearDown(self)
        Base.metadata.drop_all()
        app.close_app()
        
    
    @patch('ADSWorker.pipeline.ClaimsImporter.ClaimsImporter.publish', return_value=None)
    def test_import_worker(self, *args):
        """
        Receives claims from ADSWS; creates a record in the database
        and publishes into a queue
        """
        
        worker = workers.ClaimsImporter.ClaimsImporter()
        worker.process_payload([{
                'orcidid': '0000-0003-2686-9241',
                'bibcode': 'foo',
                'status': 'claimed'
        }, {
                'orcidid': '0000-0003-2686-9242',
                'bibcode': 'foo',
                'status': 'claimed'
        }])
        self.assertDictContainsSubset(
            {'status': 'claimed', 'bibcode': 'foo', 'provenance': 'ClaimsImporter', 'orcidid': '0000-0003-2686-9241', 'id': 1},
             worker.publish.call_args_list[0][0][0])
        self.assertDictContainsSubset(
            {'status': 'claimed', 'bibcode': 'foo', 'provenance': 'ClaimsImporter', 'orcidid': '0000-0003-2686-9242', 'id': 2},
             worker.publish.call_args_list[1][0][0])

    
    
    @patch('ADSWorker.matcher.retrieve_orcid', return_value={'status': None, 
                                           'name': u'Stern, D K', 
                                           'facts': {u'author': [u'Stern, D', u'Stern, D K', u'Stern, Daniel'], u'orcid_name': [u'Stern, Daniel'], u'author_norm': [u'Stern, D'], u'name': u'Stern, D K'}, 
                                           'orcidid': u'0000-0003-2686-9241', 
                                           'id': 1, 
                                           'account_id': None,
                                           'created': '2009-09-03T20:56:35.450686Z',
                                           'updated': '2009-09-03T20:56:35.450689Z'
                                           })
    @patch('ADSWorker.pipeline.ClaimsIngester.ClaimsIngester.publish', return_value=None)
    def test_ingest_worker(self, *args):
        """
        Updates our knowledge about orcid and pushes updated claim to the queue
        """
        
        worker = workers.ClaimsIngester.ClaimsIngester()
        worker.process_payload({'status': 'claimed', 
                                'bibcode': 'foo', 
                                'provenance': 'ClaimsImporter', 
                                'orcidid': '0000-0003-2686-9241', 
                                'id': 1})
        
        self.assertDictContainsSubset(
                                {'status': 'claimed', 
                                'bibcode': 'foo', 
                                'provenance': 'ClaimsImporter', 
                                'orcidid': '0000-0003-2686-9241', 
                                'id': 1,
                                'name': 'Stern, D K',
                                'author': [u'Stern, D', u'Stern, D K', u'Stern, Daniel'], 
                                'orcid_name': [u'Stern, Daniel'], 
                                'author_norm': [u'Stern, D'],
                                'author_id': 1,
                                'account_id': None,
                                'author_status': None
                                },
             worker.publish.call_args_list[0][0][0])
        
        
    @patch('ADSWorker.matcher.retrieve_orcid', return_value={'status': 'blacklisted', 
                                           'name': u'Stern, D K', 
                                           'facts': {u'author': [u'Stern, D', u'Stern, D K', u'Stern, Daniel'], u'orcid_name': [u'Stern, Daniel'], u'author_norm': [u'Stern, D'], u'name': u'Stern, D K'}, 
                                           'orcidid': u'0000-0003-2686-9241', 
                                           'id': 1, 
                                           'account_id': None,
                                           'created': '2009-09-03T20:56:35.450686Z',
                                           'updated': '2009-09-03T20:56:35.450689Z'
                                           })
    @patch('ADSWorker.pipeline.ClaimsIngester.ClaimsIngester.publish', return_value=None)
    def test_ingest_worker_blacklisted_author(self, *args):
        """
        Updates our knowledge about orcid and pushes updated claim to the queue
        """
        
        worker = workers.ClaimsIngester.ClaimsIngester()
        worker.process_payload({'status': 'claimed', 
                                'bibcode': 'foo', 
                                'provenance': 'ClaimsImporter', 
                                'orcidid': '0000-0003-2686-9241', 
                                'id': 1})
        
        self.assertFalse(worker.publish.called)
        
        
if __name__ == '__main__':
    unittest.main()    
