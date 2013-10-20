import requests
import json
import datetime
import time
import bson


class Beddit:
    APIBASE = 'https://api.beddit.com/api2/'
    JSON_HEADER = {'content-type': 'application/json'}

    def __init__(self, username, password):
        self.logindata = {'username': username, 'password': password}
        self.s = False
        self.users = False

    def _checkUsername(self, username):
        if not username and not self.users:
            raise Exception('No valid users have been retrieved.'
                            ' Check the output of getUsers() and retry')
            return False
        elif not username:
            return self.users[0]['username']
        return str(username)

    def _parseJSONResponse(self, response):
        if response.status_code != 200:
            return False
        ret = False
        try:
            ret = response.json()
        except Exception:
            pass
        return ret

    def login(self):
        self.s = requests.Session()
        r = self.s.post('https://api.beddit.com/login',
                        data=self.logindata,
                        allow_redirects=False)
        if (not 'set-cookie' in r.headers or
                r.headers['set-cookie'].find('appsessionid') < 0):
            return False
        # Populate list of users as a convinient to later method calls
        self.getUsers()
        return True

    def getUsers(self):
        r = self.s.get(Beddit.APIBASE+'user')
        if r.status_code != 200:
            return False
        try:
            self.users = r.json()
        except Exception:
            self.users = False
        return self.users

    def getUserInfo(self, username=False):
        username = self._checkUsername(username)
        r = self.s.get(Beddit.APIBASE+'user/'+username)
        return self._parseJSONResponse(r)

    def updateUserInfo(self, updatedDict, username=False):
        username = self._checkUsername(username)
        # NOTE - we're not checking the dict data is valid
        r = self.s.put(Beddit.APIBASE+'user/'+username,
                       headers=Beddit.JSON_HEADER,
                       data=json.dumps(updatedDict))
        return self._parseJSONResponse(r)

    def getDeviceInfo(self, username=False):
        username = self._checkUsername(username)
        r = self.s.get(Beddit.APIBASE+'user/'+username+'/device')
        return self._parseJSONResponse(r)

    # Not implementing the device POST and DELETE methods
    # also somewhat hesitant to offer ability to DELETE a device and drop data

    def getNights(self, startDate=datetime.date(2000, 1, 1),
                  endDate=datetime.date.fromtimestamp(time.time()),
                  username=False):
        username = self._checkUsername(username)
        if not (type(startDate) == datetime.date or
                type(startDate) == datetime.datetime):
            raise Exception('startDate must be a date or datetime object')
            return False
        if not (type(endDate) == datetime.date or
                type(startDate) == datetime.datetime):
            raise Exception('startDate must be a date or datetime object')
            return False
        r = self.s.get(Beddit.APIBASE+'user/'+username +
                       '/timeline?start=%04d-%02d-%02d&end=%04d-%02d-%02d' %
                       (startDate.year, startDate.month, startDate.day,
                        endDate.year, endDate.month, endDate.day))
        return self._parseJSONResponse(r)

    def getDetailedInfo(self, date=datetime.date.fromtimestamp(time.time()),
                        username=False, numpy=False):
        username = self._checkUsername(username)
        if not (type(date) == datetime.date or
                type(date) == datetime.datetime):
            raise Exception('date must be a date or datetime object')
            return False
        r = self.s.get(Beddit.APIBASE+'user/'+username +
                       '/%04d/%02d/%02d/sleep' %
                       (date.year, date.month, date.day))
        data = self._parseJSONResponse(r)
        if not data or not numpy:
            return data
        import numpy as np
        start = datetime.datetime.strptime(data['local_start_time'],
                                           "%Y-%m-%dT%H:%M:%S")
        # recreate the actigram data as a numpy array
        # numpy refuses to make a recarray if the data is a list of lists
        # so we need to re-create the dataset as a list of tuples.
        if 'minutely_actigram' in data:
            activity = []
            for i in range(0, len(data['minutely_actigram'])):
                activity.append((start+(datetime.timedelta(0, i*60)),
                                data['minutely_actigram'][i]))
            activity = np.array(activity, dtype=np.dtype(
                [('time', datetime.datetime), ('activity', '<i4')]
            ))
            data['minutely_actigram'] = activity
        # recreate the noise data as a numpy array
        if 'noise_measurements' in data:
            noise = []
            for row in data['noise_measurements'][0]:
                noise.append((datetime.datetime.strptime(row[0],
                             "%Y-%m-%dT%H:%M:%S"), row[1]))
            noise = np.array(noise, dtype=np.dtype(
                [('time', datetime.datetime), ('noise', '<f8')]
            ))
            data['noise_measurements'] = noise
        # recreate the luminosity data as a numpy array
        if 'luminosity_measurements' in data:
            luminosity = []
            for row in data['luminosity_measurements'][0]:
                luminosity.append((datetime.datetime.strptime(row[0],
                                  "%Y-%m-%dT%H:%M:%S"), row[1]))
            luminosity = np.array(luminosity, dtype=np.dtype(
                [('time', datetime.datetime), ('light', '<f8')]
            ))
            data['luminosity_measurements'] = luminosity
        # recreate the sleep stage data as a numpy array
        if 'sleep_stages' in data:
            stages = []
            for row in data['sleep_stages']:
                stages.append((datetime.datetime.strptime(row[0],
                              "%Y-%m-%dT%H:%M:%S"), row[1]))
            stages = np.array(stages, dtype=np.dtype(
                [('time', datetime.datetime), ('stage', '|U1')]
            ))
            data['sleep_stages'] = stages
        # recreate the heart rate data as a numpy array
        if 'averaged_heart_rate_curve' in data:
            heart_rate = []
            for chunk in data['averaged_heart_rate_curve']:
                for row in chunk:
                    heart_rate.append((datetime.datetime.strptime(row[0],
                                      "%Y-%m-%dT%H:%M:%S"), row[1]))
            heart_rate = np.array(heart_rate, dtype=np.dtype(
                [('time', datetime.datetime), ('heart_rate', '<f8')]
            ))
            data['averaged_heart_rate_curve'] = heart_rate
        # recreate the temperature data as a numpy array
        if 'temperature_measurements' in data:
            temperature = []
            for row in data['temperature_measurements'][0]:
                temperature.append((datetime.datetime.strptime(row[0],
                                   "%Y-%m-%dT%H:%M:%S"), row[1]))
            temperature = np.array(temperature, dtype=np.dtype(
                [('time', datetime.datetime), ('temp', '<f8')]
            ))
            data['temperature_measurements'] = temperature
        # add a time axis to the heart rate histogram data
        if 'minutely_heart_rate_histogram' in data:
            histograms = np.array(data['minutely_heart_rate_histogram'])
            data['minutely_heart_rate_histogram'] = histograms
        return data

    def getResults(self, date=datetime.date.fromtimestamp(time.time()),
                   username=False, numpy=False):
        username = self._checkUsername(username)
        if not (type(date) == datetime.date or
                type(date) == datetime.datetime):
            raise Exception('date must be a date or datetime object')
            return False
        r = self.s.get(Beddit.APIBASE+'user/'+username +
                       '/%04d/%02d/%02d/results' %
                       (date.year, date.month, date.day))
        data = self._parseJSONResponse(r)
        data['interval_start'] = datetime.datetime.strptime(
            data['interval_start'], "%Y-%m-%dT%H:%M:%S")
        data['interval_end'] = datetime.datetime.strptime(
            data['interval_end'], "%Y-%m-%dT%H:%M:%S")
        data['last_analysis_end_time'] = datetime.datetime.strptime(
            data['last_analysis_end_time'], "%Y-%m-%dT%H:%M:%S")
        if not data or not numpy:
            return data
        import numpy as np
        # recreate the respiration data as a numpy array
        if 'respiration' in data:
            respiration = []
            for row in data['respiration']:
                respiration.append(tuple(row))
            respiration = np.array(respiration, dtype=([
                                  ('time', '<f8'),
                                  ('src', '<U3'),
                                  ('min_interval', '<f8'),
                                  ('max_interval', '<f8'),
                                  ('amplitude', '<f8')
            ]))
            data['respiration'] = respiration
        # recreate the presence data as a numpy array
        if 'presence' in data:
            presence = []
            for row in data['presence']:
                presence.append(tuple(row))
            presence = np.array(respiration, dtype=(
                [('time', '<f8'), ('presence', '<i1')]
            ))
            data['presence'] = presence
        # recreate the instant heart data as a numpy array
        if 'ihr' in data:
            heart_rate = []
            for row in data['ihr']:
                heart_rate.append(tuple(row))
            heart_rate = np.array(respiration, dtype=(
                [('time', '<f8'), ('heart_rate', '<f8')]
            ))
            data['ihr'] = heart_rate
        if 'binary_actigram' in data:
            data['binary_actigram'] = np.array(data['binary_actigram'])
        return data

    def getResultsFine(self, start, end, username=False, numpy=False):
        username = self._checkUsername(username)
        if not type(start) == datetime.datetime:
            raise Exception('start must be a datetime.datetime object')
            return False
        if not type(end) == datetime.datetime:
            raise Exception('end must be a datetime.datetime object')
            return False
        r = self.s.get(Beddit.APIBASE+'user/'+username+'/results?' +
                       'start=%04d-%02d-%02dT%02d:%02d:%02d' +
                       '&end=%04d-%02d-%02dT%02d:%02d:%02d' %
                       (start.year, start.month, start.day,
                        start.hour, start.minute, start.second,
                        end.year, end.month, end.day,
                        end.hour, end.minute, end.second))
        data = self._parseJSONResponse(r)
        data['interval_start'] = datetime.datetime.strptime(
            data['interval_start'], "%Y-%m-%dT%H:%M:%S")
        data['interval_end'] = datetime.datetime.strptime(
            data['interval_end'], "%Y-%m-%dT%H:%M:%S")
        data['last_analysis_end_time'] = datetime.datetime.strptime(
            data['last_analysis_end_time'], "%Y-%m-%dT%H:%M:%S")
        if not data or not numpy:
            return data
        import numpy as np
        # recreate the respiration data as a numpy array
        if 'respiration' in data:
            respiration = []
            for row in data['respiration']:
                respiration.append(tuple(row))
            respiration = np.array(respiration, dtype=([
                                   ('time', '<f8'),
                                   ('src', '<U3'),
                                   ('min_interval', '<f8'),
                                   ('max_interval', '<f8'),
                                   ('amplitude', '<f8')]
            ))
            data['respiration'] = respiration
        # recreate the presence data as a numpy array
        if 'presence' in data:
            presence = []
            for row in data['presence']:
                presence.append(tuple(row))
            presence = np.array(respiration, dtype=(
                [('time', '<f8'), ('presence', '<i1')]
            ))
            data['presence'] = presence
        # recreate the instant heart data as a numpy array
        if 'ihr' in data:
            heart_rate = []
            for row in data['ihr']:
                heart_rate.append(tuple(row))
            heart_rate = np.array(respiration, dtype=(
                [('time', '<f8'), ('heart_rate', '<f8')]
            ))
            data['ihr'] = heart_rate
        if 'binary_actigram' in data:
            data['binary_actigram'] = np.array(data['binary_actigram'])
        return data

    def getSignal(self, date=datetime.date.fromtimestamp(time.time()),
                  username=False, numpy=False):
        username = self._checkUsername(username)
        if not (type(date) == datetime.date or
                type(date) == datetime.datetime):
            raise Exception('date must be a date or datetime object')
            return False
        r = self.s.get(Beddit.APIBASE+'user/'+username +
                       '/%04d/%02d/%02d/signal.bson' %
                       (date.year, date.month, date.day))
        data = bson.loads(r.content)
        if not data or not numpy:
            return data
        import numpy as np
        import numpy.lib.recfunctions as recfunctions
        data['interval_start'] = datetime.datetime.strptime(
            data['interval_start'], "%Y-%m-%dT%H:%M:%S")
        data['interval_end'] = datetime.datetime.strptime(
            data['interval_end'], "%Y-%m-%dT%H:%M:%S")
        for key in data['channels']:
            for key in data['channels']:
                if 'sample_data' in data['channels'][key]:
                    dataset = data['channels'][key]['sample_data']
                    rate = data['channels'][key]['sample_rate']
                    sample_data = np.fromstring(dataset, np.dtype(
                                                [(str(key), np.int16)]))
                    xaxis = np.linspace(0.0,
                                        float(len(sample_data))/float(rate),
                                        float(len(sample_data)))
                    dataset = recfunctions.append_fields(sample_data,
                                                         'time',
                                                         xaxis,
                                                         usemask=False)
                    data['channels'][key]['sample_data'] = dataset
        return data
