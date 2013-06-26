# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack LLC
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import keystone.common.sql as sql
import uuid
import datetime
import cPickle
from sqlalchemy import or_
from sqlalchemy import and_
import sqlalchemy.sql.expression as expression
from sqlalchemy import func


class ResourcesModel(sql.ModelBase):
    __tablename__ = 'resources'
    id = sql.Column(sql.String(64), primary_key=True)
    name = sql.Column(sql.String(255), unique=False, nullable=False)
    parameters = sql.Column(sql.Text, unique=False, nullable=False)
    child_identity = sql.Column(sql.Text, unique=False, nullable=False)
    type = sql.Column(sql.Enum('ABSOLUTE', 'COUNTABLE', 'RESERVABLE'),
                      nullable=False)
    purge_quota_after = sql.Column(sql.BigInt, nullable=False)
    created_at = sql.Column(sql.DateTime, nullable=False)
    created_by = sql.Column(sql.Text, nullable=False)
    closed_at = sql.Column(sql.DateTime, nullable=True)
    closed_by = sql.Column(sql.Text, nullable=True)

    def __init__(self, uuid, name, parameters, child_identity,
                 resource_type, purge_quota_after, created_at, created_by):
        self.id = uuid
        self.name = name
        self.parameters = parameters
        self.child_identity = child_identity
        self.type = resource_type
        self.purge_quota_after = purge_quota_after
        self.created_at = created_at
        self.created_by = created_by


class QuotasModel(sql.ModelBase):
    __tablename__ = 'quotas'
    id = sql.Column(sql.String(64), primary_key=True)
    resource_id = sql.Column(sql.String(64), sql.ForeignKey('resources.id'),
                             nullable=False)
    ceiling = sql.Column(sql.BigInt, nullable=False)
    available = sql.Column(sql.BigInt, nullable=True)
    created_at = sql.Column(sql.DateTime, nullable=False)
    created_by = sql.Column(sql.Text, nullable=False)
    closed_at = sql.Column(sql.DateTime, nullable=True)
    closed_by = sql.Column(sql.Text, nullable=True)

    def __init__(self, uuid, resource_id, ceiling, available, created_at,
                 created_by):
        self.id = uuid
        self.resource_id = resource_id
        self.ceiling = ceiling
        self.available = available
        self.created_at = created_at
        self.created_by = created_by


class ChildFieldDataModel(sql.ModelBase):
    __tablename__ = 'child_field_data'
    id = sql.Column(sql.String(64), primary_key=True)
    quota_id = sql.Column(sql.String(64), sql.ForeignKey('quotas.id'),
                          nullable=False)
    key = sql.Column(sql.Text, nullable=False)
    value = sql.Column(sql.Text, nullable=False)


class ParentFieldDataModel(sql.ModelBase):
    __tablename__ = 'parent_field_data'
    id = sql.Column(sql.String(64), primary_key=True)
    quota_id = sql.Column(sql.String(64), sql.ForeignKey('quotas.id'),
                          nullable=False)
    key = sql.Column(sql.Text, nullable=False)
    value = sql.Column(sql.Text, nullable=False)


class HistoryResourcesModel(sql.ModelBase):
    __tablename__ = 'h_resources'
    id = sql.Column(sql.String(64), primary_key=True)
    resource_id = sql.Column(sql.String(64), sql.ForeignKey('resources.id'),
                             nullable=False)
    updated_at = sql.Column(sql.DateTime, nullable=False)
    updated_by = sql.Column(sql.Text, nullable=False)
    remark = sql.Column(sql.Text, nullable=False)


class HistoryQuotasModel(sql.ModelBase):
    __tablename__ = 'h_quotas'
    id = sql.Column(sql.String(64), primary_key=True)
    resource_id = sql.Column(sql.String(64), sql.ForeignKey('quotas.id'),
                             nullable=False)
    updated_at = sql.Column(sql.DateTime, nullable=False)
    updated_by = sql.Column(sql.Text, nullable=False)
    remark = sql.Column(sql.Text, nullable=False)


class QuotaSetModel():
    child_data = dict()
    service_dict = dict()
    '''For a single child, there will be single service_dict.
    Service_dict will have services as the key
    while values being another dictionary having
    resource-names as there keys and number of resources as there values'''


class Resources(sql.Base):
    def register_resource(self, resource_name, parameters, child_identity,
                          resource_type, purge_quota_after, created_by):
        """ Registers a resource in the quota manager
        """
        if((type(parameters) is not list)):
            raise Exception(('parameters should be a list'))
        if (type(created_by) is not dict):
            raise Exception(('created_by should be a dictionary'))
        session = self.get_session()
        with session.begin():
            ref = ResourcesModel(str(uuid.uuid4()),
                           resource_name,
                           cPickle.dumps(parameters),
                           cPickle.dumps(child_identity),
                           resource_type,
                           purge_quota_after,
                           datetime.datetime.now(),
                           cPickle.dumps(created_by))
            session.add(ref)
            session.flush()
        return

    def deregister_resource(self, resource_name, closed_by):
        """ De-registers (deletes) a resource in the quota manager.
            All the corresponding quotas are also deleted
        """

        return

    def get_resource_list(self, service_name):
        """Returns list of resources registered with quota manager
           for the given service
        :param service_name: name of the service for which resources
                             are to be returned
        """
        return


class Quotas(sql.Base):
    def set_quota(self, resource_name, ceiling, child_data, parent_data,
                   created_by):
        if(type(child_data) is not dict):
            raise Exception(('child_data should be a dictionary'))
        if(type(parent_data) is not dict):
            raise Exception(('parent_data should be a dictionary'))
        if(type(created_by) is not dict):
            raise Exception(('created_by should be a dictionary'))

        session = self.get_session()
        with session.begin():
            #First check whether quota for the child already exist or not
            for key in child_data:
                oneKey = key
                oneValue = child_data[key]
                break
            ''' this subquery is for getting list of existing quota_ids
            corresponding to one of the key value pair in child_data. '''
            subquery = session.query(ChildFieldDataModel.quota_id).filter(and_
                        (ChildFieldDataModel.quota_id == QuotasModel.id,
                        QuotasModel.resource_id == ResourcesModel.id,
                        ResourcesModel.name == resource_name,
                        ChildFieldDataModel.key == oneKey,
                        ChildFieldDataModel.value == oneValue))
            initial_query = session.query(ChildFieldDataModel.quota_id,
                                   func.count(ChildFieldDataModel.quota_id).\
                                   label('count'))
            key_value_match = []
            for key in child_data:
                key_value_match.append(expression.\
                    and_(ChildFieldDataModel.key == key,
                        ChildFieldDataModel.value == child_data[key]))
            query = initial_query.filter(or_(*key_value_match)).\
                        filter(ChildFieldDataModel.quota_id.in_(subquery)).\
                        group_by(ChildFieldDataModel.quota_id)
            result = query.one()
            if (result.count == len(child_data)):
                raise Exception('quota already exist')
            result = session.query(ResourcesModel.id).\
                        filter(ResourcesModel.name == resource_name).one()
            resource_id = result.id

            refQ = QuotasModel(str(uuid.uuid4()),
                           resource_id=resource_id,
                           ceiling=ceiling,
                           available=-1,
                           created_at=datetime.datetime.now(),
                           created_by=cPickle.dumps(created_by))
            session.add(refQ)
            quota_id = refQ.id
            #quota_id will be used for child field data and parent field data

            for key in child_data:
                refC = ChildFieldDataModel(id=str(uuid.uuid4()),
                                        quota_id=quota_id,
                                        key=key,
                                        value=child_data[key])
                session.add(refC)

            for key in parent_data:
                refC = ParentFieldDataModel(id=str(uuid.uuid4()),
                                        quota_id=quota_id,
                                        key=key,
                                        value=parent_data[key])
                session.add(refC)
            session.flush()
        return

    def get_quota(self, resource_name, child_data):
        """ Gets the quota applicable to the specified child
        for the given resource

        :param resource_name: name of the resource in the format
                              <service-name>.<resouce-name>
        :param child: details of the entity for which quota is requested.
                      It should be a dictionary
        """
        return

    def get_quota_multiple_resources(self, service_list, list_resource_lists,
                                    child_data):
        """ Gets the quota applicable to the specified child
        for the given resources in the given services

        :param service_list: list of services
        :param list_resource_lists: list of lists of resources for services in
                                    service_list for which quota is requested
        :param child: details of the entity for which quota is requested.
                      It should be a dictionary
        """
        return

    def update_quota(self, resource_name, child_data, ceiling_to_update_to,
                     parent_data):
        """ Updates the quota applicable to the specified child
        for the given resource

        :param resource_name: name of the resource in the format
                              <service-name>.<resouce-name>
        :param child: details of the entity for which quota is to be updated.
                      It should be a dictionary
        :param ceiling_to_update_to: value of the quota to update to.
        :param parent_data: details of the entity calling this method.
                            It should be a dictionary and should exactly match
                            the parent_data already present in the db.
        """
        return

    def delete_quota(self, resource_name, child_data, parent_data):
        """ Deletes the quota applicable to the specified child
        for the given resource.

        :param resource_name: name of the resource in the format
                              <service-name>.<resouce-name>
        :param child: details of the entity for which quota is to be deleted.
                      It should be a dictionary
        :param parent_data: details of the entity calling this method.
                            It should be a dictionary and should exactly match
                            the parent_data already present in the db.
        """
        return
