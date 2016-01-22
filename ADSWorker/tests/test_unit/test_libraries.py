#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unit tests of the project. Each function related to the workers individual tools
are tested in this suite. There is no communication.
"""


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

from ADSWorker.tests import test_base
from ADSWorker import matcher, app, updater, importer, utils
from ADSWorker.models import AuthorInfo, ClaimsLog, Records, Base

class TestMatcherUpdater(test_base.TestUnit):
    """
    Tests the worker's methods
    """
    
    def tearDown(self):
        test_base.TestUnit.tearDown(self)
        Base.metadata.drop_all()
        app.close_app()
    
    def create_app(self):
        app.init_app({
            'SQLALCHEMY_URL': 'sqlite:///',
            'SQLALCHEMY_ECHO': False
        })
        Base.metadata.bind = app.session.get_bind()
        Base.metadata.create_all()
        return app
    
    def test_get_date(self):
        """Check we always work with UTC dates"""
        
        d = utils.get_date()
        self.assertTrue(d.tzname() == 'UTC')
        
        d1 = utils.get_date('2009-09-04T01:56:35.450686Z')
        self.assertTrue(d1.tzname() == 'UTC')
        self.assertEqual(d1.isoformat(), '2009-09-04T01:56:35.450686+00:00')
        
        d2 = utils.get_date('2009-09-03T20:56:35.450686-05:00')
        self.assertTrue(d2.tzname() == 'UTC')
        self.assertEqual(d2.isoformat(), '2009-09-04T01:56:35.450686+00:00')

        d3 = utils.get_date('2009-09-03T20:56:35.450686')
        self.assertTrue(d3.tzname() == 'UTC')
        self.assertEqual(d3.isoformat(), '2009-09-03T20:56:35.450686+00:00')

    def test_models(self):
        """Check serialization into JSON"""
        
        claim = ClaimsLog(bibcode='foo', orcidid='bar',
                          created='2009-09-03T20:56:35.450686Z')
        self.assertDictEqual(claim.toJSON(),
             {'status': None, 'bibcode': 'foo', 'created': '2009-09-03T20:56:35.450686+00:00', 'provenance': 'None', 'orcidid': 'bar', 'id': None})
        
        ainfo = AuthorInfo(orcidid='bar',
                          created='2009-09-03T20:56:35.450686Z')
        
        self.assertDictEqual(ainfo.toJSON(),
             {'status': None, 'updated': None, 'name': None, 'created': '2009-09-03T20:56:35.450686+00:00', 'facts': {}, 'orcidid': 'bar', 'id': None, 'account_id': None})
        
        rec = Records(bibcode='foo', created='2009-09-03T20:56:35.450686Z')

        self.assertDictEqual(rec.toJSON(),
             {'bibcode': 'foo', 'created': '2009-09-03T20:56:35.450686+00:00', 'updated': None, 'processed': None, 'claims': {}, 'id': None})
    
    @httpretty.activate
    def test_harvest_author_info(self):
        """
        We have to be able to verify orcid against orcid api
        and also collect data from SOLR (author names)
        """
        
        orcidid = '0000-0003-2686-9241'
        
        httpretty.register_uri(
            httpretty.GET, self.app.config['API_ORCID_PROFILE_ENDPOINT'] % orcidid,
            content_type='application/json',
            body=open(os.path.join(self.app.config['TEST_UNIT_DIR'], 'stub_data', orcidid + '.orcid.json')).read())
        httpretty.register_uri(
            httpretty.GET, self.app.config['API_SOLR_QUERY_ENDPOINT'],
            content_type='application/json',
            body=open(os.path.join(self.app.config['TEST_UNIT_DIR'], 'stub_data', orcidid + '.solr.json')).read())
        
        data = matcher.harvest_author_info(orcidid)
        self.assertDictEqual(data, {'orcid_name': [u'Stern, Daniel'],
                                    'author': [u'Stern, D', u'Stern, D K', u'Stern, Daniel'],
                                    'author_norm': [u'Stern, D'],
                                    'name': u'Stern, D K'
                                    })
        
    
    def test_create_orcid(self):
        """Has to create AuthorInfo and populate it, but not add to database"""
        
        with mock.patch('ADSWorker.matcher.harvest_author_info', return_value= {'orcid_name': [u'Stern, Daniel'],
                                    'author': [u'Stern, D', u'Stern, D K', u'Stern, Daniel'],
                                    'author_norm': [u'Stern, D'],
                                    'name': u'Stern, D K'
                                    }
                ) as context:
            res = matcher.create_orcid('0000-0003-2686-9241')
            self.assertIsInstance(res, AuthorInfo)
            self.assertEqual(res.name, 'Stern, D K')
            self.assertEqual(res.orcidid, '0000-0003-2686-9241')
            self.assertEqual(res.facts, '{"orcid_name": ["Stern, Daniel"], "author_norm": ["Stern, D"], "name": "Stern, D K", "author": ["Stern, D", "Stern, D K", "Stern, Daniel"]}')
            
            self.assertTrue(self.app.session.query(AuthorInfo).first() is None)

 
    def test_retrive_orcid(self):
        """Has to find and load/or create ORCID data"""
        
        with mock.patch('ADSWorker.matcher.harvest_author_info', return_value= {'orcid_name': [u'Stern, Daniel'],
                                    'author': [u'Stern, D', u'Stern, D K', u'Stern, Daniel'],
                                    'author_norm': [u'Stern, D'],
                                    'name': u'Stern, D K'
                                    }
                ) as context:
            author = matcher.retrieve_orcid('0000-0003-2686-9241')
            self.assertDictContainsSubset({'status': None, 
                                           'name': u'Stern, D K', 
                                           'facts': {u'author': [u'Stern, D', u'Stern, D K', u'Stern, Daniel'], u'orcid_name': [u'Stern, Daniel'], u'author_norm': [u'Stern, D'], u'name': u'Stern, D K'}, 
                                           'orcidid': u'0000-0003-2686-9241', 
                                           'id': 1, 
                                           'account_id': None}, 
                                          author)
        
            self.assertTrue(self.app.session.query(AuthorInfo).first().orcidid, '0000-0003-2686-9241')
        

    def test_update_record(self):
        """
        Update ADS document with the claim info

        :return: no return
        """
        
        doc = {
            'bibcode': '2015ApJ...799..123B', 
            'authors': [
              "Barrière, Nicolas M.",
              "Krivonos, Roman",
              "Tomsick, John A.",
              "Bachetti, Matteo",
              "Boggs, Steven E.",
              "Chakrabarty, Deepto",
              "Christensen, Finn E.",
              "Craig, William W.",
              "Hailey, Charles J.",
              "Harrison, Fiona A.",
              "Hong, Jaesub",
              "Mori, Kaya",
              "Stern, Daniel",
              "Zhang, William W."
            ]
        }
        updater.update_record(
          doc,
          {
           'bibcode': '2015ApJ...799..123B', 
           'orcidid': '0000-0003-2686-9241',
           'accnt_id': '10',
           'orcid_name': [u'Stern, Daniel'],
           'author': [u'Stern, D', u'Stern, D K', u'Stern, Daniel'],
           'author_norm': [u'Stern, D'],
           'name': u'Stern, D K' 
          }                          
        )
        self.assertEqual(doc['verified'], 
            ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '0000-0003-2686-9241', '-'])
        
        updater.update_record(
          doc,
          {
           'bibcode': '2015ApJ...799..123B', 
           'orcidid': '0000-0003-2686-9241',
           'accnt_id': '10',
           'orcid_name': [u'Stern, Daniel'],
           'author': [u'Stern, D', u'Stern, D K', u'Stern, Daniel'],
           'author_norm': [u'Stern, D'],
           'name': u'Stern, D K',
           'status': 'removed'
          }                          
        )
        self.assertEqual(doc['verified'], 
            ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'])
        
        
    def test_find_author_position(self):
        """
        Given the ORCID ID, and information about author name, 
        we have to identify the position of the author from
        the list of supplied names

        :return: no return
        """
        
        res = updater.find_orcid_position([
              "Barrière, Nicolas M.",
              "Krivonos, Roman",
              "Tomsick, John A.",
              "Bachetti, Matteo",
              "Boggs, Steven E.",
              "Chakrabarty, Deepto",
              "Christensen, Finn E.",
              "Craig, William W.",
              "Hailey, Charles J.",
              "Harrison, Fiona A.",
              "Hong, Jaesub",
              "Mori, Kaya",
              "Stern, Daniel",
              "Zhang, William W."
            ],
          ['Stern, D.', 'Stern, Daniel']                          
        )
        self.assertEqual(res, 12)
        
    def test_update_database(self):
        """Inserts a record (of claims) into the database"""
        updater.record_claims('bibcode', {'verified': ['foo', '-', 'bar'], 'unverified': ['-', '-', '-']})
        with app.session_scope() as session:
            r = session.query(Records).filter_by(bibcode='bibcode').first()
            self.assertEquals(json.loads(r.claims), {'verified': ['foo', '-', 'bar'], 'unverified': ['-', '-', '-']})
            self.assertTrue(r.created == r.updated)
            self.assertFalse(r.processed)
            
        updater.record_claims('bibcode', {'verified': ['foo', 'zet', 'bar'], 'unverified': ['-', '-', '-']})
        with app.session_scope() as session:
            r = session.query(Records).filter_by(bibcode='bibcode').first()
            self.assertEquals(json.loads(r.claims), {'verified': ['foo', 'zet', 'bar'], 'unverified': ['-', '-', '-']})
            self.assertTrue(r.created != r.updated)
            self.assertFalse(r.processed)
        
        updater.mark_processed('bibcode')
        with app.session_scope() as session:
            r = session.query(Records).filter_by(bibcode='bibcode').first()
            self.assertTrue(r.processed)
            
            
    def test_importer_import_recs(self):
        """It should know how to import bibcode:orcidid pairs
        :return None
        """
        
        fake_file = BytesIO("\n".join([
                                 "b123456789123456789\t0000-0000-0000-0001",
                                 "b123456789123456789\t0000-0000-0000-0002\tarxiv",
                                 "b123456789123456789\t0000-0000-0000-0003\tarxiv\tclaimed",
                                 "b123456789123456789\t0000-0000-0000-0004\tfoo        \tcreated\t2008-09-03T20:56:35.450686Z",
                                 "b123456789123456789\t0000-0000-0000-0005",
                                 "b123456789123456789\t0000-0000-0000-0006",
                                 "b123456789123456789\t0000-0000-0000-0004\tfoo        \tupdated\t2009-09-03T20:56:35.450686Z",
                                ]))
        with mock.patch('ADSWorker.importer.open', return_value=fake_file, create=True
                ) as context:
            importer.import_recs(__file__)
            self.assertTrue(len(self.app.session.query(ClaimsLog).all()) == 7)

        fake_file = BytesIO('\n'.join([
                                "b123456789123456789\t0000-0000-0000-0001",
                                "b123456789123456789\t0000-0000-0000-0002\tarxiv"]))

        with mock.patch('ADSWorker.importer.open', return_value=fake_file, create=True
                ) as context:
            c = []
            importer.import_recs(__file__, collector=c)
            self.assertTrue(len(c) == 2)
        
    
    def test_insert_claim(self):
        """
        It should be able to create a series of claims
        """
        r = importer.insert_claims([
                    {'bibcode': 'b123456789123456789',
                     'orcidid': '0000-0000-0000-0001',
                     'provenance' : 'ads test'},
                    {'bibcode': 'b123456789123456789',
                     'orcidid': '0000-0000-0000-0001',
                     'status' : 'updated'},
                    importer.create_claim(bibcode='b123456789123456789', 
                                          orcidid='0000-0000-0000-0001', 
                                          status='removed')
                ])
        self.assertEquals(len(r), 3)
        
        self.assertTrue(len(self.app.session.query(ClaimsLog)
                            .filter_by(bibcode='b123456789123456789').all()) == 3)
        
if __name__ == '__main__':
    unittest.main()
