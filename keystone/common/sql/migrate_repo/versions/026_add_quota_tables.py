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

import sqlalchemy as sql


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = sql.MetaData()
    meta.bind = migrate_engine

    resources_table = sql.Table(
        'resources',
        meta,
        sql.Column('id', sql.String(64), primary_key=True),
        sql.Column('name', sql.String(255), unique=False, nullable=False),
        sql.Column('parameters', sql.TEXT, unique=False, nullable=False),
        sql.Column('child_identity', sql.TEXT, unique=False, nullable=False),
        sql.Column('type', sql.Enum('ABSOLUTE','COUNTABLE','RESERVABLE'), nullable=False),
        sql.Column('purge_quota_after', sql.BIGINT, nullable=False),
        sql.Column('created_at', sql.DATETIME, nullable=False),
        sql.Column('created_by', sql.TEXT, nullable=False),
        sql.Column('closed_at', sql.DATETIME, nullable=True),
        sql.Column('closed_by', sql.TEXT, nullable=True))
    resources_table.create(migrate_engine, checkfirst=True)
    
    quotas_table = sql.Table(
        'quotas',
        meta,
        sql.Column('id', sql.String(64), primary_key=True),
        sql.Column('resource_id', sql.String(64), sql.ForeignKey('resources.id'), nullable=False),
        sql.Column('ceiling', sql.BIGINT, nullable=False),
        sql.Column('available', sql.BIGINT, nullable=True),
        sql.Column('created_at', sql.DATETIME, nullable=False),
        sql.Column('created_by', sql.TEXT, nullable=False),
        sql.Column('closed_at', sql.DATETIME, nullable=True),
        sql.Column('closed_by', sql.TEXT, nullable=True))
    quotas_table.create(migrate_engine, checkfirst=True)
    
    child_field_data_table = sql.Table(
        'child_field_data',
        meta,
        sql.Column('id', sql.String(64), primary_key=True),
        sql.Column('quota_id', sql.String(64), sql.ForeignKey('quotas.id'), nullable=False),
        sql.Column('key', sql.TEXT, nullable=False),
        sql.Column('value', sql.TEXT, nullable=False))
    child_field_data_table.create(migrate_engine, checkfirst=True)

    parent_field_data_table = sql.Table(
        'parent_field_data',
        meta,
        sql.Column('id', sql.String(64), primary_key=True),
        sql.Column('quota_id', sql.String(64), sql.ForeignKey('quotas.id'), nullable=False),
        sql.Column('key', sql.TEXT, nullable=False),
        sql.Column('value', sql.TEXT, nullable=False))
    parent_field_data_table.create(migrate_engine, checkfirst=True)


    h_resources_table = sql.Table(
        'h_resources',
        meta,
        sql.Column('id', sql.String(64), primary_key=True),
        sql.Column('resource_id', sql.String(64), sql.ForeignKey('resources.id'), nullable=False),
        sql.Column('updated_at', sql.DATETIME, nullable=False),
        sql.Column('updated_by', sql.TEXT, nullable=False),
        sql.Column('remark', sql.TEXT, nullable=False))
    h_resources_table.create(migrate_engine, checkfirst=True)
    
    h_quotas_table = sql.Table(
        'h_quotas',
        meta,
        sql.Column('id', sql.String(64), primary_key=True),
        sql.Column('quota_id', sql.String(64), sql.ForeignKey('quotas.id'), nullable=False),
        sql.Column('updated_by', sql.TEXT, nullable=False),
        sql.Column('remark', sql.TEXT, nullable=False))
    h_quotas_table.create(migrate_engine, checkfirst=True)
    
def downgrade(migrate_engine):
    meta = sql.MetaData()
    meta.bind = migrate_engine
    # Operations to reverse the above upgrade go here.
    for table_name in ['resources','quotas','h_resources','h_quotas',
                       'child_field_data', 'parent_field_data']:
        table = sql.Table(table_name, meta, autoload=True)
        table.drop()
