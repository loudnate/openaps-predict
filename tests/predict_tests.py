from datetime import datetime
import json
import os
import unittest

from openapscontrib.predict.predict import Schedule
from openapscontrib.predict.predict import calculate_iob
from openapscontrib.predict.predict import future_glucose


def get_file_at_path(path):
    return "{}/{}".format(os.path.dirname(os.path.realpath(__file__)), path)


class FutureGlucoseTestCase(unittest.TestCase):
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

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'glucose': 150.0}, glucose[0])
        self.assertDictEqual({'date': '2015-07-13T16:10:00', 'glucose': 110.0}, glucose[-1])

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

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-07-13T10:00:00', 'glucose': 150.0}, glucose[0])
        self.assertDictEqual({'date': '2015-07-13T15:10:00', 'glucose': 70.0}, glucose[-1])

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

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-07-13T11:00:00', 'glucose': 150.0}, glucose[0])
        self.assertDictEqual({'date': '2015-07-13T11:30:00', 'glucose': 150.0}, glucose[6])
        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'glucose': 150.0}, glucose[12])

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

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'glucose': 150.0}, glucose[0])
        self.assertEqual('2015-07-13T17:10:00', glucose[-1]['date'])
        self.assertAlmostEqual(110.0, glucose[-1]['glucose'], delta=2)

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

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-07-13T11:00:00', 'glucose': 150.0}, glucose[0])
        self.assertDictEqual({'date': '2015-07-13T11:30:00', 'glucose': 150.0}, glucose[6])
        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'glucose': 150.0}, glucose[12])

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

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-07-15T18:40:00', 'glucose': 190.0}, glucose[-1])

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

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule']),
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertEqual('2015-07-17T17:10:00', glucose[-1]['date'])
        self.assertAlmostEqual(130, glucose[-1]['glucose'], delta=1)

    def test_no_input_history(self):
        normalized_history = []

        normalized_glucose = [
            {
                "date": "2015-07-17T12:00:00",
                "sgv": 150
            }
        ]

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule']),
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertEqual('2015-07-17T16:10:00', glucose[-1]['date'])
        self.assertEqual(150, glucose[-1]['glucose'])

    def test_no_input_glucose(self):
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
        ]

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule']),
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertListEqual([], glucose)

    def test_single_bolus_with_excercise_marker(self):
        normalized_history = [
            {
                "start_at": "2015-07-13T12:05:00",
                "description": "JournalEntryExerciseMarker",
                "end_at": "2015-07-13T12:05:00",
                "amount": 1,
                "type": "Exercise",
                "unit": "event"
            },
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

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'glucose': 150.0}, glucose[0])
        self.assertDictEqual({'date': '2015-07-13T16:15:00', 'glucose': 110.0}, glucose[-1])

    def test_fake_unit(self):
        normalized_history = [
            {
                "start_at": "2015-09-07T22:23:08",
                "description": "JournalEntryExerciseMarker",
                "end_at": "2015-09-07T22:23:08",
                "amount": 1,
                "type": "Exercise",
                "unit": "beer"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-13T12:00:00",
                "sgv": 150
            }
        ]

        with self.assertRaises(ValueError):
            glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
            )


class CalculateIOBTestCase(unittest.TestCase):
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

        iob = calculate_iob(
            normalized_history,
            4
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 0.0, 'unit': 'U'}, iob[0])
        self.assertDictEqual({'date': '2015-07-13T12:10:00', 'amount': 1.0, 'unit': 'U'}, iob[2])
        self.assertDictEqual({'date': '2015-07-13T16:10:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])

    def test_datetime_rounding(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:02:37",
                "end_at": "2015-07-13T12:02:37",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        iob = calculate_iob(
            normalized_history,
            4
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 0.0, 'unit': 'U'}, iob[0])
        self.assertDictEqual({'date': '2015-07-13T12:10:00', 'amount': 0.0, 'unit': 'U'}, iob[2])
        self.assertDictContainsSubset({'date': '2015-07-13T12:15:00', 'unit': 'U'}, iob[3])
        self.assertAlmostEqual(1.0, iob[3]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T16:15:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])

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

        iob = calculate_iob(
            normalized_history,
            4
        )

        self.assertDictEqual({'date': '2015-07-13T10:00:00', 'amount': 0.0, 'unit': 'U'}, iob[0])
        self.assertDictContainsSubset({'date': '2015-07-13T10:10:00'}, iob[2])
        self.assertAlmostEqual(1.0, iob[2]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-07-13T11:00:00'}, iob[12])
        self.assertAlmostEqual(0.84, iob[12]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-07-13T12:00:00'}, iob[24])
        self.assertAlmostEqual(1.37, iob[24]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T15:10:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])

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

        iob = calculate_iob(
            normalized_history,
            4
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 0.0, 'unit': 'U'}, iob[0])
        self.assertDictEqual({'date': '2015-07-13T17:10:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])
        self.assertEqual('2015-07-13T14:00:00', iob[24]['date'])
        self.assertAlmostEqual(0.75, iob[24]['amount'], delta=0.01)

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

        iob = calculate_iob(
            normalized_history,
            4
        )

        self.assertDictEqual({'date': '2015-07-15T14:30:00', 'amount': 0.0, 'unit': 'U'}, iob[0])
        self.assertDictEqual({'date': '2015-07-15T18:40:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])

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

        iob = calculate_iob(
            normalized_history,
            4,
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertDictEqual({'date': '2015-07-17T17:10:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])
        self.assertDictEqual({'date': '2015-07-17T16:40:00', 'amount': 0.0, 'unit': 'U'}, iob[-7])
        self.assertDictContainsSubset({'date': '2015-07-17T12:40:00', 'unit': 'U'}, iob[8])
        self.assertAlmostEqual(0.56, iob[8]['amount'], delta=0.01)

    def test_no_input_history(self):
        normalized_history = []

        iob = calculate_iob(
            normalized_history,
            4,
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertListEqual([], iob)

    def test_fake_unit(self):
        normalized_history = [
            {
                "start_at": "2015-09-07T22:23:08",
                "description": "JournalEntryExerciseMarker",
                "end_at": "2015-09-07T22:23:08",
                "amount": 1,
                "type": "Exercise",
                "unit": "beer"
            }
        ]

        iob = calculate_iob(
            normalized_history,
            4
        )

        self.assertDictEqual({'date': '2015-09-07T22:20:00', 'amount': 0.0, 'unit': 'U'}, iob[0])
        self.assertDictEqual({'date': '2015-09-08T02:35:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])
