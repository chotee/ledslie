from ledslie.content.rain import RainContent


class TestRain(object):
    def test_init(self):
        endpoint = None
        factory = None
        rain = RainContent(endpoint, factory)
        return rain

    def test_create_forcast(self):
        rain = self.test_init()
        data = [
            [0, '00:00'],
            [0, '00:05'],
            [0, '00:10'],
        ]
        assert "Dry until 00:10" == rain.create_forcast(data)

        data = [
            [0, '00:00'],
            [100, '00:05'],
            [0, '00:10'],
        ]
        assert "Rain at 00:05" == rain.create_forcast(data)

        data = [
            [100, '00:00'],
            [100, '00:05'],
            [0  , '00:10'],
            [50 , '00:15'],
        ]
        assert "Rain stops: 00:10" == rain.create_forcast(data)

        data = [
            [100, '00:00'],
            [100, '00:05'],
            [70 , '00:10'],
            [50 , '00:15'],
        ]
        assert "Rain Rain Rain" == rain.create_forcast(data)


    def test_parse_forecast_results(self):
        rain = self.test_init()
        assert 24 == len(rain.parse_forecast_results(sample1))
        assert [0, '09:40'] == rain.parse_forecast_results(sample1)[1]
        assert [0, '09:45'] == rain.parse_forecast_results(sample1)[2]

sample1 = b"""000|09:35\r\n000|09:40\r\n000|09:45\r\n000|09:50\r\n000|09:55\r\n000|10:00\r\n077|10:05\r\n096|10:10\r\n
000|10:15\r\n000|10:20\r\n102|10:25\r\n099|10:30\r\n077|10:35\r\n077|10:40\r\n109|10:45\r\n106|10:50\r\n
108|10:55\r\n087|11:00\r\n000|11:05\r\n000|11:10\r\n000|11:15\r\n000|11:20\r\n000|11:25\r\n000|11:30\r\n"""
