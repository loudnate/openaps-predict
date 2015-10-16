from datetime import datetime
import json
import os
import unittest

from openapscontrib.predict.predict import Schedule
from openapscontrib.predict.predict import calculate_carb_effect
from openapscontrib.predict.predict import calculate_glucose_from_effects
from openapscontrib.predict.predict import calculate_insulin_effect
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

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictContainsSubset({'date': '2015-07-13T16:10:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(110.0, glucose[-1]['amount'])

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

        self.assertDictEqual({'date': '2015-07-13T10:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictContainsSubset({'date': '2015-07-13T15:10:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(70.0, glucose[-1]['amount'])

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

        self.assertDictEqual({'date': '2015-07-13T11:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[1])
        self.assertDictContainsSubset({'date': '2015-07-13T16:10:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(110.0, glucose[-1]['amount'])

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

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertEqual('2015-07-13T17:10:00', glucose[-1]['date'])
        self.assertAlmostEqual(110.0, glucose[-1]['amount'])

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

        self.assertDictEqual({'date': '2015-07-13T11:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[1])
        self.assertDictContainsSubset({'date': '2015-07-13T13:00:00', 'unit': 'mg/dL'}, glucose[13])
        self.assertAlmostEqual(146.87, glucose[13]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-07-13T17:10:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(110.0, glucose[-1]['amount'])

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

        self.assertDictContainsSubset({'date': '2015-07-15T18:40:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(190.0, glucose[-1]['amount'])

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

        self.assertDictContainsSubset({'date': '2015-07-17T17:10:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(130, glucose[-1]['amount'], delta=1)

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

        self.assertEqual([{'date': '2015-07-17T12:00:00', 'amount': 150.0, 'unit': 'mg/dL'}], glucose)

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

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictContainsSubset({'date': '2015-07-13T16:15:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(110.0, glucose[-1]['amount'])

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
                "date": "2015-09-07T23:00:00",
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

        self.assertDictEqual({'date': '2015-09-07T23:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictEqual({'date': '2015-09-08T02:35:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[-1])


class CalculateCarbEffectTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(get_file_at_path("fixtures/read_insulin_sensitivies.json")) as fp:
            cls.insulin_sensitivities = json.load(fp)

        with open(get_file_at_path("fixtures/read_carb_ratios.json")) as fp:
            cls.carb_ratios = json.load(fp)

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

        effect = calculate_carb_effect(
            normalized_history,
            Schedule(self.carb_ratios['schedule']),
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-07-15T17:40:00', 'amount': 40.0, 'unit': 'mg/dL'}, effect[-1])

    def test_no_input_history(self):
        normalized_history = []

        effect = calculate_carb_effect(
            normalized_history,
            Schedule(self.carb_ratios['schedule']),
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertListEqual([], effect)

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

        effect = calculate_carb_effect(
            normalized_history,
            Schedule(self.carb_ratios['schedule']),
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-09-07T22:20:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[0])
        self.assertDictEqual({'date': '2015-09-08T01:35:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[-1])


class CalculateInsulinEffectTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[0])
        self.assertDictEqual({'date': '2015-07-13T16:10:00', 'amount': -40.0, 'unit': 'mg/dL'}, effect[-1])

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

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[0])
        self.assertDictContainsSubset({'date': '2015-07-13T12:15:00', 'unit': 'mg/dL'}, effect[3])
        self.assertAlmostEqual(-0.12, effect[3]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T16:15:00', 'amount': -40.0, 'unit': 'mg/dL'}, effect[-1])

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

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-07-13T10:00:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[0])
        self.assertDictEqual({'date': '2015-07-13T15:10:00', 'amount': -80.0, 'unit': 'mg/dL'}, effect[-1])

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

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictContainsSubset({'date': '2015-07-13T12:10:00', 'unit': 'mg/dL'}, effect[2])
        self.assertAlmostEqual(-1.06, effect[2]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T17:10:00', 'amount': -40.0, 'unit': 'mg/dL'}, effect[-1])
        self.assertEqual('2015-07-13T13:50:00', effect[22]['date'])
        self.assertAlmostEqual(-13.37, effect[24]['amount'], delta=0.01)

    def test_two_square_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T07:00:00",
                "end_at": "2015-07-13T08:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            },
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T13:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictContainsSubset({'date': '2015-07-13T07:10:00', 'unit': 'mg/dL'}, effect[2])
        self.assertAlmostEqual(-1.06, effect[2]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T17:10:00', 'amount': -80.0, 'unit': 'mg/dL'}, effect[-1])
        self.assertEqual('2015-07-13T08:50:00', effect[22]['date'])
        self.assertAlmostEqual(-13.37, effect[24]['amount'], delta=0.01)

    def test_overlapping_basals(self):
        normalized_history = [
            {
                "type": "TempBasal",
                "start_at": "2015-07-13T08:00:00",
                "end_at": "2015-07-13T09:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            },
            {
                "type": "TempBasal",
                "start_at": "2015-07-13T07:00:00",
                "end_at": "2015-07-13T08:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictContainsSubset({'date': '2015-07-13T07:10:00', 'unit': 'mg/dL'}, effect[2])
        self.assertAlmostEqual(-1.07, effect[2]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T13:10:00', 'amount': -80.0, 'unit': 'mg/dL'}, effect[-1])
        self.assertEqual('2015-07-13T08:50:00', effect[22]['date'])
        self.assertAlmostEqual(-16.50, effect[24]['amount'], delta=0.01)

    def test_counteracting_basals(self):
        normalized_history = [
            {
                "type": "TempBasal",
                "start_at": "2015-07-13T08:00:00",
                "end_at": "2015-07-13T09:00:00",
                "amount": -1.0,
                "unit": "U/hour"
            },
            {
                "type": "TempBasal",
                "start_at": "2015-07-13T07:00:00",
                "end_at": "2015-07-13T08:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictContainsSubset({'date': '2015-07-13T07:10:00', 'unit': 'mg/dL'}, effect[2])
        self.assertAlmostEqual(-1.06, effect[2]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T13:10:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[-1])
        self.assertEqual('2015-07-13T08:50:00', effect[22]['date'])
        self.assertAlmostEqual(-10.25, effect[24]['amount'], delta=0.01)

    def test_insulin_effect_with_sensf_change(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-15T14:30:00",
                "end_at": "2015-07-15T14:30:00",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule([
                {
                    "i": 0,
                    "start": "00:00:00",
                    "sensitivity": 40,
                    "offset": 0,
                    "x": 0
                },
                {
                    "i": 1,
                    "start": "16:00:00",
                    "sensitivity": 10,
                    "offset": 450,
                    "x": 450
                }
            ])
        )

        self.assertDictEqual({'date': '2015-07-15T18:40:00', 'amount': -40.0, 'unit': 'mg/dL'}, effect[-1])

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

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertEqual('2015-07-17T17:10:00', effect[-1]['date'])
        self.assertAlmostEqual(-20.0, effect[-1]['amount'])

    def test_no_input_history(self):
        normalized_history = []

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertListEqual([], effect)

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

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-09-07T22:20:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[0])
        self.assertDictEqual({'date': '2015-09-08T02:35:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[-1])

    def test_negative_temp_basals(self):
        normalized_history = [
            {
                "amount": -0.8,
                "start_at": "2015-10-15T20:39:52",
                "description": "TempBasal: 0.0U/hour over 20min",
                "type": "TempBasal",
                "unit": "U/hour",
                "end_at": "2015-10-15T20:59:52"
            },
            {
                "amount": -0.75,
                "start_at": "2015-10-15T20:34:34",
                "description": "TempBasal: 0.05U/hour over 5min",
                "type": "TempBasal",
                "unit": "U/hour",
                "end_at": "2015-10-15T20:39:34"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-10-15T20:30:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[0])

        self.assertDictContainsSubset({'date': '2015-10-15T22:40:00', 'unit': 'mg/dL'}, effect[26])
        self.assertAlmostEqual(5.97, effect[26]['amount'], delta=0.01)

        self.assertEqual('2015-10-16T01:10:00', effect[-1]['date'])
        self.assertAlmostEqual(13.16, effect[-1]['amount'], delta=0.01)


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

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 1.0, 'unit': 'U'}, iob[0])
        self.assertDictContainsSubset({'date': '2015-07-13T12:20:00', 'unit': 'U'}, iob[4])
        self.assertAlmostEqual(0.98, iob[4]['amount'], delta=0.01)
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
        self.assertDictContainsSubset({'date': '2015-07-13T12:15:00', 'unit': 'U'}, iob[3])
        self.assertAlmostEqual(0.99, iob[3]['amount'], delta=0.01)
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

        self.assertDictEqual({'date': '2015-07-13T10:00:00', 'amount': 1.0, 'unit': 'U'}, iob[0])
        self.assertDictContainsSubset({'date': '2015-07-13T10:20:00'}, iob[4])
        self.assertAlmostEqual(0.98, iob[4]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-07-13T11:00:00'}, iob[12])
        self.assertAlmostEqual(1.85, iob[12]['amount'], delta=0.01)
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

        self.assertDictContainsSubset({'date': '2015-07-13T12:10:00', 'unit': 'U'}, iob[2])
        self.assertAlmostEqual(0.083, iob[2]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T17:10:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])
        self.assertEqual('2015-07-13T13:50:00', iob[22]['date'])
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
        self.assertDictEqual({'date': '2015-07-17T12:00:00', 'amount': 0.0, 'unit': 'U'}, iob[0])
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
