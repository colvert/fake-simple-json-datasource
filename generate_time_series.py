#!/usr/bin/python
#
# This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
import logging
import json
import os
import requests
import time
import yaml

from datetime import datetime

"""
The goal is to generate the time series from the Test API for the supervizion
"""

#list_of_pods = ['pod4-orange-heat1', 'pod4-orange-heat2', 'pod4-orange-oom1']
list_of_pods = ['pod4-orange-heat1']
robot_healthcheck = {'name': 'robot_healthcheck',
                     'weight': 0.5,
                     'details': ['Basic SDNGC Health Check',
                                 'Basic A&AI Health Check',
                                 'Basic Policy Health Check',
                                 'Basic MSO Health Check',
                                 'Basic ASDC Health Check',
                                 'Basic APPC Health Check',
                                 'Basic Portal Health Check',
                                 'Basic Message Router Health Check',
                                 'Basic VID Health Check',
                                 'Basic Microservice Bus Health Check',
                                 'Basic Clamp Health Check']}
# robot_healthcheck_test = {'name': 'robot_healthcheck',
#                      'weight': 0.5,
#                      'details': ['Basic SDNGC Health Check']}
robot_api = {'name': 'robot_api',
             'weight':0.2,
             'details': ['catalog API Health Check',
                         'nslcm API Health Check',
                         'resmgr API Health Check',
                         'usecaseui-gui API Health Check',
                         'vnflcm API Health Check',
                         'vnfmgr API Health Check',
                         'vnfres API Health Check',
                         'workflow API Health Check']}
robot_dcae = {'name': 'robot_dcae',
              'weight': 0.1,
              'details': ['Basic DCAE Health Check']}
robot_multicloud = {'name': 'robot_multicloud',
                    'weight': 0.1,
                    'details': ['multicloud API Health Check',
                                'multicloud-ocata API Health Check',
                                'multicloud-titanium_cloud API Health Check',
                                'multicloud-vio API Health Check']}
robot_3rdparty = {'name': 'robot_3rdparty',
                  'weight': 0.1,
                  'details': ['emsdriver API Health Check',
                              'gvnfmdriver API Health Check',
                              'huaweivnfmdriver API Health Check',
                              'ztesdncdriver API Health Check',
                              'ztevmanagerdriver API Health Check']}

NB_TESTS_TAKEN_INTO_ACCOUNT = 2
NB_DAYS_OF_TEST_TAKEN_INTO_ACCOUNT = 30
TESTAPI_URL = "http://10.0.2.5:8021/api/v1/results"
PROXY = {
    'http': "socks5://127.0.0.1:8080",
    'https': "socks5://127.0.0.1:8080",
    }
#list_of_tests = [robot_healthcheck,robot_api,robot_dcae,robot_multicloud,robot_3rdparty]
#list_of_tests = [robot_healthcheck, robot_api]
list_of_tests = [robot_healthcheck,robot_api]


class OnapTestTS(object):
    def __init__(self, **kwargs):
        """Initialize OnapTestTS object."""
        super(OnapTestTS, self).__init__()
        # get param from env variables
        list_of_tests = kwargs["list_of_tests"]
        ts_init = []
        for macro_test in list_of_tests:
            for test in macro_test['details']:
                ts_init.append({"target": test,"datapoints":[]})
        self.test_ts = ts_init

    def add_point_to_ts(self, name, value):
        for elt in self.test_ts:
            if elt['target'] == name:
                if name == 'catalog API Health Check':
                    print("Add {} to {}", value, name)
                elt['datapoints'].append(value)
                break

    def add_score(self, pod, score):
        the_time = int(time.time()*1000)
        self.test_ts.append({"target": pod,"datapoints":[[score,the_time]]})

    def add_scores(self):
        for pod in list_of_pods:
            the_time = int(time.time()*1000)
            score = calculate_global_pod_score(pod)
            self.test_ts.append({"target": pod,"datapoints":[[score,the_time]]})


    def get(self):
        return self.test_ts

    def generate_time_series(self, case, pod):
        results = getApiResults(case, pod, nb_days=NB_DAYS_OF_TEST_TAKEN_INTO_ACCOUNT)

        # print(results['results'])
        for s in results:
            tmp_res = s['details']['tests']
            # print(tmp_res)
            # print("------------")
            # print(len(tmp_res))
            print(case)
            for res in tmp_res:
                timestamp = format_time_for_ts(res['starttime'])
                if case == 'catalog API Health Check':
                    print("on rajoute une ligne....pour catalog")
                if "PASS" in res['status']:
                    self.add_point_to_ts(res['name'],[1, timestamp])
                else:
                    self.add_point_to_ts(res['name'],[0, timestamp])


def format_time_for_ts(date_time):
    pattern = '%Y%m%d %H:%M:%S.%f'
    epoch = int(time.mktime(time.strptime(date_time, pattern)))*1000
    return epoch

def calculate_pod_score_per_case(case, pod):
    results = getApiResults(case, pod)
    count_pass = str(results).count("PASS")
    count_fail = str(results).count("FAIL")
    try:
        return round(count_pass*100/(count_pass + count_fail))
    except ZeroDivisionError:
        return 0

def calculate_global_pod_score(pod):
    # calculation with ponderation...
    tot_scores = 0
    for s in list_of_tests:
        tot_scores += s['weight']*calculate_pod_score_per_case(s['name'], pod)
    return tot_scores

def getApiResults(case, pod, **kwargs):
    """
    Get Results by calling the API

    criteria is to consider N last results for the case success criteria
    """
    results = json.dumps([])

    url = TESTAPI_URL + "?case=" + case + "&pod=" + pod
    try:
        url += "&period=" + str(kwargs['nb_days'])
    except KeyError:
        url += "&last=" + str(NB_TESTS_TAKEN_INTO_ACCOUNT)

    print(url)
    response = requests.get(url, proxies=PROXY)

    # get nb of pages if pagination
    try:
        res_json = json.loads(response.content)
        nb_pages = res_json["pagination"]["total_pages"]
        results = res_json['results']
        if nb_pages > 1:
            for page in range(2, nb_pages + 1):
                response = requests.get(url + "&page=" + str(page),
                                        proxies=PROXY)
                res_json = json.loads(response.content)
                results += res_json['results']
    except Exception:  # pylint: disable=broad-except
        print("Error when retrieving results form API")

    return results

def export_series(data, pod):
    """
    Generate time series
    """
    file_name = 'series_' + pod + '.json'
    with open(file_name, 'w') as outfile:
        json.dump(data, outfile)

def export_results():
    """
    Generate time series
    """
    file_name = 'scores_pod.csv'
    data = ""
    date_time = datetime.now()
    with open(file_name, 'w') as outfile:
        for pod in list_of_pods:
            score = calculate_global_pod_score(pod)
            data = str(date_time) + "," + pod + "," + str(score) + "\n"
            outfile.write(data)


# ----------------------------------------------------------------------------

# toto = calculate_pod_score_per_case("robot_healthcheck", "pod4-orange-heat1")
# toto = calculate_global_pod_score("pod4-orange-heat2")


# generate cvv file


# toto_time = format_time_for_ts("20180219 10:39:07.028")
# toto = initiate_ts_results()
# print(toto)
# add_point_to_ts(toto,"Basic SDNGC Health Check", [1.0,toto_time])
# print(toto)


# print(onap_ts.get())
# onap_ts.generate_time_series("robot_healthcheck","pod4-orange-heat2")
# print("------------------------------")
# print(onap_ts.get())

# print(str(onap_ts.get()))
# onap_ts.add_point_to_ts("Basic SDNGC Health Check", [1.0,toto_time])
for pod in list_of_pods:
    onap_ts = OnapTestTS(list_of_tests=list_of_tests)
    onap_ts.add_scores()
    for test in list_of_tests:
        onap_ts.generate_time_series(test['name'],pod)
    export_series(onap_ts.get(), pod)
    print(str(onap_ts.get()))
    print("------------------------------")
export_results()
