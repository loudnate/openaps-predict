from datetime import datetime
import json
import os
import unittest

from openapscontrib.predict.predict import foo, Schedule


def get_file_at_path(path):
    return "{}/{}".format(os.path.dirname(os.path.realpath(__file__)), path)


class FooTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(get_file_at_path("fixtures/read_carb_ratios.json")) as fp:
            cls.carb_ratios = json.load(fp)

        with open(get_file_at_path("fixtures/read_insulin_sensitivies.json")) as fp:
            cls.insulin_sensitivities = json.load(fp)

    def test_single_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T12:00:00",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-13T12:00:00",
                "sgv": 150
            }
        ]

        glucose = foo(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertEqual(('2015-07-13T12:10:00', 150.0), glucose[0])
        self.assertEqual(('2015-07-13T16:10:00', 110.0), glucose[-1])

    def test_multiple_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T10:00:00",
                "end_at": "2015-07-13T10:00:00",
                "amount": 1.0,
                "unit": "U"
            },
            {
                "type": "Bolus",
                "start_at": "2015-07-13T11:00:00",
                "end_at": "2015-07-13T11:00:00",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-13T10:00:00",
                "sgv": 150
            }
        ]

        glucose = foo(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertEqual(('2015-07-13T10:10:00', 150.0), glucose[0])
        self.assertEqual(('2015-07-13T15:10:00', 70.0), glucose[-1])

    def test_future_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T12:00:00",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-13T11:00:00",
                "sgv": 150
            }
        ]

        glucose = foo(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertEqual(('2015-07-13T11:10:00', 150.0), glucose[0])
        self.assertEqual(('2015-07-13T11:40:00', 150.0), glucose[6])
        self.assertEqual(('2015-07-13T12:10:00', 150.0), glucose[12])

    def test_square_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T13:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-13T12:00:00",
                "sgv": 150
            }
        ]

        glucose = foo(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertEqual(('2015-07-13T12:10:00', 150.0), glucose[0])
        self.assertEqual('2015-07-13T17:10:00', glucose[-1][0])
        self.assertAlmostEqual(110.0, glucose[-1][1], delta=2)

    def test_future_square_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T13:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-13T11:00:00",
                "sgv": 150
            }
        ]

        glucose = foo(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertEqual(('2015-07-13T11:10:00', 150.0), glucose[0])
        self.assertEqual(('2015-07-13T11:40:00', 150.0), glucose[6])
        self.assertEqual(('2015-07-13T12:10:00', 150.0), glucose[12])

    def test_carb_completion_with_ratio_change(self):
        normalized_history = [
            {
                "type": "Meal",
                "start_at": "2015-07-15T14:30:00",
                "end_at": "2015-07-15T14:30:00",
                "amount": 9,
                "unit": "g"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-15T14:30:00",
                "sgv": 150
            }
        ]

        glucose = foo(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertEqual(('2015-07-15T18:40:00', 190.0), glucose[-1])

    def test_basal_dosing_end(self):
        normalized_history = [
            {
                "type": "TempBasal",
                "start_at": "2015-07-17T12:00:00",
                "end_at": "2015-07-17T13:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-17T12:00:00",
                "sgv": 150
            }
        ]

        glucose = foo(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule']),
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertEqual('2015-07-17T17:10:00', glucose[-1][0])
        self.assertAlmostEqual(130, glucose[-1][1], delta=1)
