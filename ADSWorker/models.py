# -*- coding: utf-8 -*-

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
import datetime
import json
from .utils import get_date

Base = declarative_base()

class KeyValue(Base):
    __tablename__ = 'storage'
    key = Column(String(255), primary_key=True)
    value = Column(Text)

class AuthorInfo(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True)
    orcidid = Column(String(19), unique=True)
    name = Column(String(255))
    facts = Column(Text)
    status = Column(String(255))
    account_id = Column(Integer)
    created = Column(TIMESTAMP, default=get_date)
    updated = Column(TIMESTAMP, default=get_date)
    
    def toJSON(self):
        return {'id': self.id, 'orcidid': self.orcidid,
                'name': self.name, 'facts': self.facts and json.loads(self.facts) or {},
                'status': self.status, 'account_id': self.account_id,
                'created': self.created and get_date(self.created).isoformat() or None, 'updated': self.updated and get_date(self.updated).isoformat() or None
                }
    
    
class ClaimsLog(Base):
    __tablename__ = 'claims'
    id = Column(Integer, primary_key=True)
    orcidid = Column(String(19))
    bibcode = Column(String(19))
    status = Column(String(255))
    provenance = Column(String(255))
    created = Column(TIMESTAMP, default=get_date)
    
    def toJSON(self):
        return {'id': self.id, 'orcidid': self.orcidid,
                'bibcode': self.bibcode, 'status': self.status,
                'provenance': unicode(self.provenance), 'created': self.created and get_date(self.created).isoformat() or None
                }

    
class Records(Base):
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True)
    bibcode = Column(String(19))
    claims = Column(Text)
    created = Column(TIMESTAMP)
    updated = Column(TIMESTAMP, default=get_date)
    processed = Column(TIMESTAMP)
    
    def toJSON(self):
        return {'id': self.id, 'bibcode': self.bibcode,
                'claims': self.claims and json.loads(self.claims) or {},
                'created': self.created and get_date(self.created).isoformat() or None, 'updated': self.updated and get_date(self.updated).isoformat() or None, 
                'processed': self.processed and get_date(self.processed).isoformat() or None
                }

    
