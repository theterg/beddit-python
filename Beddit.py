class Beddit:
    APIBASE = 'https://api.beddit.com/api2/'
    JSON_HEADER = {'content-type': 'application/json'}

    def __init__(self, username, password):
        self.logindata = {'username': username, 'password': password}
        self.s = False
        self.users = False

    def _checkUsername(self, username):
        if not username and not self.users:
            raise Exception('No valid users have been retrieved.  Check the output of getUsers() and retry')
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
        except JSONDecodeError as e:
            pass
        return ret

    def login(self):
        self.s = requests.Session()
        r = self.s.post('https://api.beddit.com/login', data=self.logindata, allow_redirects=False)
        if not 'set-cookie' in r.headers or r.headers['set-cookie'].find('appsessionid') < 0:
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
        except JSONDecodeError as e:
            self.users = False
        return self.users

    def getUserInfo(self, username=False):
        username = self._checkUsername(username)
        r = self.s.get(Beddit.APIBASE+'user/'+username)
        return self._parseJSONResponse(r)

    def updateUserInfo(self, updatedDict, username=False):
        username = self._checkUsername(username)
        # NOTE - we're not checking the dict data is valid - letting the API handle that.
        r = self.s.put(Beddit.APIBASE+'user/'+username, headers=Beddit.JSON_HEADER, data=json.dumps(updatedDict))
        return self._parseJSONResponse(r)

    def getDeviceInfo(self, username=False):
        username = self._checkUsername(username)
        r = self.s.get(Beddit.APIBASE+'user/'+username+'/device')
        return self._parseJSONResponse(r)

    # Not implementing the device POST and DELETE methods - don't have enough beddits to test
    # also somewhat hesitant to offer ability to DELETE a device and drop all of a users data...

    def getNights(self, startDate=datetime.date(2000,1, 1), endDate=datetime.date.fromtimestamp(time.time()), username=False):
        username = self._checkUsername(username)
        if not (type(startDate) == datetime.date or type(startDate) == datetime.datetime):
            raise Exception('startDate must be a datetime.date or datetime.datetime object')
            return False
        if not (type(endDate) == datetime.date or type(startDate) == datetime.datetime):
            raise Exception('startDate must be a datetime.date or datetime.datetime object')
            return False
        r = self.s.get(Beddit.APIBASE+'user/'+username+'/timeline?start=%04d-%02d-%02d&end=%04d-%02d-%02d' %
                       (startDate.year, startDate.month, startDate.day,
                        endDate.year, endDate.month, endDate.day))
        return self._parseJSONResponse(r)

    def getDetailedInfo(self, date=datetime.date.fromtimestamp(time.time()), username=False, numpy=False, useDates=True):
        username = self._checkUsername(username)
        if not (type(date) == datetime.date or type(date) == datetime.datetime):
            raise Exception('date must be a datetime.date or datetime.datetime object')
            return False
        r = self.s.get(Beddit.APIBASE+'user/'+username+'/%04d/%02d/%02d/sleep' %
                       (date.year, date.month, date.day))
        data = self._parseJSONResponse(r)
        if not data or not numpy:
            return data
        import numpy as np
        start = np.datetime64(data['local_start_time'])
        actigram = np.array(data['minutely_actigram'])
        noise = np.array(data['noise_measurements'])
        luminosity = np.array(data['luminosity_measurements'])
        sleep_stages = np.array(data['sleep_stages'])

    def getDetailedInfoRaw(self, date=datetime.date.fromtimestamp(time.time()), username=False, numpy=False, useDates=True):
        username = self._checkUsername(username)
        if not (type(date) == datetime.date or type(date) == datetime.datetime):
            raise Exception('date must be a datetime.date or datetime.datetime object')
            return False
        r = self.s.get(Beddit.APIBASE+'user/'+username+'/%04d/%02d/%02d/sleep' %
                       (date.year, date.month, date.day))
        return r