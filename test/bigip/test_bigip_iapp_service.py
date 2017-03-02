#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2017 F5 Networks Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import yaml

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.module_utils.f5_utils import (
    AnsibleF5Client
)
from library.bigip_iapp_service import (
    Parameters,
    ModuleManager,
    ArgumentSpec
)


fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)



def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except:
        pass

    fixture_data[path] = data
    return data


class TestParameters(unittest.TestCase):

    def test_module_parameters_keys(self):
        args = load_fixture('iapp_service_parameters_f5_http.json')
        p = Parameters(args)

        # Assert the top-level keys
        assert p.name == 'http_example'
        assert p.partition == 'Common'
        assert p.template == '/Common/f5.http'

    def test_module_parameters_lists(self):
        args = load_fixture('iapp_service_parameters_f5_http.json')
        p = Parameters(args)

        assert 'lists' in p._values

        assert p.lists[0]['name'] == 'irules__irules'
        assert p.lists[0]['encrypted'] == 'no'
        assert len(p.lists[0]['value']) == 1
        assert p.lists[0]['value'][0] == '/Common/lgyft'

        assert p.lists[1]['name'] == 'net__client_vlan'
        assert p.lists[1]['encrypted'] == 'no'
        assert len(p.lists[1]['value']) == 1
        assert p.lists[1]['value'][0] == '/Common/net2'

    def test_module_parameters_tables(self):
        args = load_fixture('iapp_service_parameters_f5_http.json')
        p = Parameters(args)

        assert 'tables' in p._values

        assert 'columnNames' in p.tables[0]
        assert len(p.tables[0]['columnNames']) == 1
        assert p.tables[0]['columnNames'][0] == 'name'

        assert 'name' in p.tables[0]
        assert p.tables[0]['name'] == 'pool__hosts'

        assert 'rows' in p.tables[0]
        assert len(p.tables[0]['rows']) == 1
        assert 'row' in p.tables[0]['rows'][0]
        assert len(p.tables[0]['rows'][0]['row']) == 1
        assert p.tables[0]['rows'][0]['row'][0] == 'demo.example.com'

        assert len(p.tables[1]['rows']) == 2
        assert 'row' in p.tables[0]['rows'][0]
        assert len(p.tables[1]['rows'][0]['row']) == 2
        assert p.tables[1]['rows'][0]['row'][0] == '10.1.1.1'
        assert p.tables[1]['rows'][0]['row'][1] == '0'
        assert p.tables[1]['rows'][1]['row'][0] == '10.1.1.2'
        assert p.tables[1]['rows'][1]['row'][1] == '0'

    def test_module_parameters_variables(self):
        args = load_fixture('iapp_service_parameters_f5_http.json')
        p = Parameters(args)

        assert 'variables' in p._values
        assert len(p.variables) == 34

        # Assert one configuration value
        assert 'name' in p.variables[0]
        assert 'value' in p.variables[0]
        assert p.variables[0]['name'] == 'afm__policy'
        assert p.variables[0]['value'] == '/#do_not_use#'

        # Assert a second configuration value
        assert 'name' in p.variables[0]
        assert 'value' in p.variables[0]
        assert p.variables[0]['name'] == 'afm__policy'
        assert p.variables[0]['value'] == '/#do_not_use#'

    def test_api_parameters_variables(self):
        args = dict(
            variables=[
                dict(
                    name="client__http_compression",
                    encrypted="no",
                    value="/#create_new#"
                )
            ]
        )
        p = Parameters(args)
        assert p.variables[0]['name'] == 'client__http_compression'

    def test_api_parameters_tables(self):
        args = dict(
            tables=[
                {
                    "name": "pool__members",
                    "columnNames": [
                        "addr",
                        "port",
                        "connection_limit"
                    ],
                    "rows": [
                        {
                            "row": [
                                "12.12.12.12",
                                "80",
                                "0"
                            ]
                        },
                        {
                            "row": [
                                "13.13.13.13",
                                "443",
                                10
                            ]
                        }
                    ]
                }
            ]
        )
        p = Parameters(args)
        assert p.tables[0]['name'] == 'pool__members'
        assert p.tables[0]['columnNames'] == ['addr','port','connection_limit']
        assert len(p.tables[0]['rows']) == 2
        assert 'row' in p.tables[0]['rows'][0]
        assert 'row' in p.tables[0]['rows'][1]
        assert p.tables[0]['rows'][0]['row'] == ['12.12.12.12', '80', '0']
        assert p.tables[0]['rows'][1]['row'] == ['13.13.13.13', '443', '10']


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    @patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
           return_value=True)
    def test_create_service(self, mgmt):
        parameters = load_fixture('iapp_service_parameters_f5_http.json')
        set_module_args(dict(
            name='foo',
            template='f5.http',
            parameters=parameters,
            state='present',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.exit_json = lambda x: True
        mm.exists = lambda: False
        mm.create_on_device = lambda: True

        results = mm.exec_module()

        print(results)
        assert results['changed'] is True
