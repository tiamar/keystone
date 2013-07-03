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
    quota_id = sql.Column(sql.String(64), sql.ForeignKey('quotas.id'),
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
            raise TypeError(('parameters should be a list'))
        if (type(created_by) is not dict):
            raise TypeError(('created_by should be a dictionary'))
        session = self.get_session()
        with session.begin():
            # Check no resource should exist with name resource_name
            ref = session.query(ResourcesModel.name)\
                         .filter(ResourcesModel.name == resource_name)\
                         .filter(ResourcesModel.closed_at == None)
            result = ref.all()
            if (len(result) == 0):
                # i.e. resource is not registered
                # so, register it!
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
            else:
                raise Exception('resource is already registered')
        return

    def deregister_resource(self, resource_name, parameters, child_identity,
                            resource_type, purge_quota_after, created_by):
        """ De-registers (deletes) a resource in the quota manager.
            All the corresponding quotas are also deleted
        """

        return

    def update_resource(self, resource_name, parameters, child_identity,
                            resource_type, purge_quota_after):
        """ Updates a resource related fields in the quota manager.
        """

        return

    def get_resource_details(self, resource_name):
        session = self.get_session()
        ref = session.query(ResourcesModel)\
                         .filter(ResourcesModel.name == resource_name)\
                         .filter(ResourcesModel.closed_at == None)
        result = ref.one()
        resource_details = {}
        resource_details["name"] = resource_name
        resource_details["parameters"] = cPickle.loads(str(result.parameters))
        resource_details["child_identity"] = cPickle\
                                             .loads(str(result.child_identity))
        resource_details["resource_type"] = str(result.type)
        resource_details["purge_quota_after"] = result.purge_quota_after
        resource_details["created_at"] = result.created_at
        resource_details["created_by"] = cPickle.loads(str(result.created_by))
        return resource_details

    def get_parameters(self, resource_name):
        return

    def get_child_identity(self, resource_name):
        return

    def get_resource_type(self, resource_name):
        return

    def get_purge_quota_after(self, resource_name):
        return

    def get_resource_list(self, service_name):
        """Returns list of resources registered with quota manager
           for the given service
        :param service_name: name of the service for which resources
                             are to be returned
        """
        return


class Quotas(sql.Base):
    def __get_quota_ids_for_child(self, child_data, service,
                                resource=None,
                                get_only_query=False):
        if(type(child_data) is not dict):
            raise TypeError('child_data should be a dictionary')
        if((type(service) is not str) & (type(service) is not list)):
            raise TypeError('service should be either string or list')
        session = self.get_session()
        with session.begin():
            key_value_match = []
            for key in child_data:
                key_value_match.append(expression.\
                    and_(ChildFieldDataModel.key == key,
                        ChildFieldDataModel.value == child_data[key]))
            resource_match = []
            if (resource is None):
                if (type(service) is str):
                    resource_match.append(ResourcesModel.name.like
                                          (service + ".%"))
                else:
                    for one_service in service:
                        resource_match.append(ResourcesModel.name.like
                                              (one_service + ".%"))
            else:
                resource_match.append(ResourcesModel.name ==
                                      (service + "." + resource))
            subquery = session.query(ChildFieldDataModel.quota_id).filter(and_
                        (ChildFieldDataModel.quota_id == QuotasModel.id,
                        QuotasModel.resource_id == ResourcesModel.id))\
                        .filter(or_(*resource_match))\
                        .filter(or_(*key_value_match))\
                        .filter(QuotasModel.closed_at == None)\
                        .filter(ResourcesModel.closed_at == None)\
                        .group_by(ChildFieldDataModel.quota_id)\
                        .having(func.count(ChildFieldDataModel.quota_id)\
                               == len(child_data))

            query = session.query(ChildFieldDataModel.quota_id)\
                        .filter(ChildFieldDataModel.quota_id.in_(subquery))\
                        .group_by(ChildFieldDataModel.quota_id)\
                        .having(func.count(ChildFieldDataModel.quota_id)\
                               == len(child_data))
            if (get_only_query):
                return query
            result = query.all()
            quota_id_list = []
            for res in result:
                quota_id_list.append(str(res.quota_id))
        return quota_id_list

    def set_quota(self, resource_name, ceiling, child_data, parent_data,
                   created_by, remark=None, update_if_exist=True):
        if(type(child_data) is not dict):
            raise TypeError(('child_data should be a dictionary'))
        if(type(parent_data) is not dict):
            raise TypeError(('parent_data should be a dictionary'))
        if(type(created_by) is not dict):
            raise TypeError(('created_by should be a dictionary'))
        if(type(resource_name) is not str):
            raise TypeError(('resource_name should be a string'))
        service_resource_split = resource_name.split('.')
        if (len(service_resource_split) != 2):  # TODO Regex Check
            raise ValueError('resource_name is not correctly formatted')
        service = service_resource_split[0]
        resource = service_resource_split[1]

        session = self.get_session()
        with session.begin():
            # First check whether quota for the child already exist or not
            quota_ids = self.__get_quota_ids_for_child(child_data,
                                                     service, resource)
            if (len(quota_ids) != 0):  # record for quota exist
                if(update_if_exist == True):
                    # so update the existing record
                    # First : Check whether given parent is allowed to update
                    refP = session.query(ParentFieldDataModel.key,
                                         ParentFieldDataModel.value)\
                    .filter(ParentFieldDataModel.quota_id == quota_ids[0])
                    result = refP.all()
                    for res in result:
                        if ((res.key in parent_data) and
                            (parent_data[res.key] == res.value)):
                            continue
                        else:
                            raise Exception("given parent can't update quota")

                    result = session.query(QuotasModel.ceiling)\
                             .filter(id == quota_ids[0])\
                             .one()

                    if (remark == None):
                        remark = ""

                    historyRemark = "ceiling: "\
                                    + str(result.ceiling)\
                                    + "->"\
                                    + str(ceiling)\
                                    + ". "\
                                    + remark
                    # Update the record
                    session.query(QuotasModel)\
                    .filter(id == quota_ids[0])\
                    .update({"ceiling": ceiling})
                    # Create a history record for the same
                    ref = HistoryQuotasModel(str(uuid.uuid4()),
                              quota_id=quota_ids[0],
                              updated_at=datetime.datetime.now(),
                              updated_by=cPickle.dumps(created_by),
                              remark=historyRemark)
                    session.add(ref)
                    session.commit()
                else:
                    return None
            else:
                result = session.query(ResourcesModel.id)\
                        .filter(ResourcesModel.name == resource_name)\
                        .filter(ResourcesModel.closed_at == None)\
                        .one()
                resource_id = result.id

                refQ = QuotasModel(str(uuid.uuid4()),
                           resource_id=resource_id,
                           ceiling=ceiling,
                           available=-1,
                           created_at=datetime.datetime.now(),
                           created_by=cPickle.dumps(created_by))
                session.add(refQ)
                quota_id = refQ.id

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
                session.commit()
                service_list = []
                service_list.append(service)
        return self.get_quota_by_services(service_list, child_data)

    def get_quota_by_services(self, service_list, child_data):
        """ Gets the quota applicable to the specified child
        for all the resources in the given services

        :param service_list: list of services
        :param child: details of the entity for which quota is requested.
                      It should be a dictionary
        """
        if(type(service_list) is not list):
            raise TypeError('service_list should be a list')
        for service in service_list:
            if(type(service) is not str):
                raise TypeError('service names should be string')
        session = self.get_session()
        with session.begin():
            quota_ids = self.__get_quota_ids_for_child(child_data,
                                                       service_list,
                                                       None,
                                                       True)
            ref = session.query(ResourcesModel.name, QuotasModel.ceiling)\
                    .filter(QuotasModel.resource_id == ResourcesModel.id)\
                    .filter(QuotasModel.id.in_(quota_ids))\
                    .order_by(ResourcesModel.name)
            result = ref.all()
            service_list.sort()
            service_dict = {}
            for service in service_list:
                resources_n_quotas = {}
                for res in result:
                    service_name = res.name.split('.')[0]
                    resource_name = res.name.split('.')[1]
                    if (str(service_name) == service):
                        resources_n_quotas[str(resource_name)] = res.ceiling
                service_dict[service] = resources_n_quotas

            obj_to_return = QuotaSetModel()
            obj_to_return.child_data = child_data
            obj_to_return.service_dict = service_dict
        return obj_to_return

    def delete_quota(self, service_list, child_data, parent_data, deleted_by):
        """ Deletes the quota applicable to the specified child
        for all the resources in the mentioned services

        :param service_list: list of services
        :param child: details of the entity for which quota is to be deleted.
                      It should be a dictionary
        :param parent_data: details of the entity calling this method.
                            It should be a dictionary and should match
                            the parent_data already present in the db.
        """
        if(type(service_list) is not list):
            raise TypeError('service_list should be a list')
        for service in service_list:
            if(type(service) is not str):
                raise TypeError('service names should be string')
        if (type(deleted_by) is not dict):
            raise TypeError(('deleted_by should be a dictionary'))

        quota_values_to_be_deleted = self.get_quota_by_services(service_list,
                                                                child_data)
        session = self.get_session()
        with session.begin():
            quota_ids = self.__get_quota_ids_for_child(child_data,
                                                       service_list,
                                                       None,
                                                       True)
            for quota_id in quota_ids:
                session.query(QuotasModel)\
                    .filter_by(id=quota_id)\
                    .update({"closed_at": datetime.datetime.now(),
                             "closed_by": cPickle.dumps(deleted_by)})
        session.commit()
        return quota_values_to_be_deleted
