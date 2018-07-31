#!/usr/bin/env python
# coding=utf-8

__author__ = 'alexandruast'

import requests
import datetime
import argparse

from influxdb import InfluxDBClient


class SonarApiClient:
    def __init__(self, d_config):
        self.url = d_config['sonar_url']
        self.token = d_config['sonar_token']

    def api_query(self, meta):
        r = requests.get(self.url + meta, headers={'Authorization': 'token {}'.format(self.token)})
        return r.json()


class DBClient:
    def __init__(self, d_config):
        self.ip = d_config['influxdb_ip']
        self.port = d_config['influxdb_port']
        self.database = d_config['influxdb_database']
        self.user = d_config['influxdb_user']
        self.password = d_config['influxdb_password']

    def write_metrics(self, d_metrics):
        db_client = InfluxDBClient(
            host=self.ip,
            port=self.port,
            username=self.user,
            password=self.password,
            database=self.database
        )
        db_client.write_points(d_metrics)


def get_ids(sonar_client, meta):
    data = sonar_client.api_query(meta)
    ids = []
    for component in data['components']:
        dict = {
            'id': component['id'],
            'key': component['key']
        }
        ids.append(dict)
    return ids


def get_metrics(sonar_client, meta):
    data = sonar_client.api_query(meta)
    metrics = []
    for metric in data['metrics']:
        metrics.append(metric['key'])
    return metrics


def prepare_measures(project_id, project_key, timestamp, measures):
    d_export = []
    for measure in measures:
        d_measure = {
            "measurement": measure['metric'],
            "tags": {
                "id": project_id,
                "key": project_key
            },
            "time": timestamp,
            "fields": {
                "value": measure['value'] if ('value' in measure) else 0
            }
        }
        d_export.append(d_measure)
    return d_export


def get_measures(sonar_client, meta):
    data = sonar_client.api_query(meta)
    return data['component']['measures']


def main():

    parser = argparse.ArgumentParser(
        description='Import Sonar data to InfluxDB'
    )

    parser.add_argument('--sonar-url', help='Sonar URL', required=True)
    parser.add_argument('--sonar-token', help='Sonar AUTH Token', required=True)
    parser.add_argument('--influxdb-ip', help='InfluxDB IP Address', required=True)
    parser.add_argument('--influxdb-port', help='InfluxDB Port', default=8086, required=False)
    parser.add_argument('--influxdb-database', help='InfluxDB Database', default='sonar', required=False)
    parser.add_argument('--influxdb-user', help='InfluxDB Username', default='sonar', required=False)
    parser.add_argument('--influxdb-password', help='InfluxDB Password', required=True)

    d_config = vars(parser.parse_args())

    timestamp = datetime.datetime.utcnow().isoformat()

    sonar_client = SonarApiClient(d_config)

    ids = get_ids(sonar_client, '/api/components/search?qualifiers=TRK')
    metrics = get_metrics(sonar_client, '/api/metrics/search')

    comma_separated_metrics = ''

    for metric in metrics:
        comma_separated_metrics += metric + ','
    comma_separated_metrics = comma_separated_metrics.rstrip(',')

    for item in ids:
        project_id = item['id']
        project_key = item['key']
        print(project_key, project_id)
        component_id_query_param = 'componentId=' + project_id
        metric_key_query_param = 'metricKeys=' + comma_separated_metrics
        measures = get_measures(sonar_client, '/api/measures/component?{}&{}'.format(component_id_query_param, metric_key_query_param))
        db_client = DBClient(d_config)
        db_client.write_metrics(prepare_measures(project_id, project_key, timestamp, measures))


if __name__ == "__main__":
    main()
