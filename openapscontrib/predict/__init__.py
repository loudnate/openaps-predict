"""
predict - tools for predicting glucose trends


"""
from .version import __version__

import ast
import argparse
from datetime import datetime, timedelta
from dateutil.parser import parse
from dateutil.tz import gettz
import json
import os

from openaps.uses.use import Use

from predict import Schedule
from predict import calculate_momentum_effect
from predict import calculate_carb_effect
from predict import calculate_cob
from predict import calculate_glucose_from_effects
from predict import calculate_insulin_effect
from predict import calculate_iob
from predict import future_glucose
from predict import glucose_data_tuple


# set_config is needed by openaps for all vendors.
# set_config is used by `device add` commands so save any needed
# information.
# See the medtronic builtin module for an example of how to use this
# to save needed information to establish sessions (serial numbers,
# etc).
def set_config(args, device):
    # no special config
    return


# display_device allows our custom vendor implementation to include
# special information when displaying information about a device using
# our plugin as a vendor.
def display_device(device):
    # no special information needed to run
    return ''


# openaps calls get_uses to figure out how how to use a device using
# agp as a vendor.  Return a list of classes which inherit from Use,
# or are compatible with it:
def get_uses(device, config):
    return [
        glucose,
        glucose_from_effects,
        glucose_momentum_effect,
        scheiner_carb_effect,
        scheiner_cob,
        walsh_insulin_effect,
        walsh_iob
    ]


def _opt_date(timestamp):
    """Parses a date string if defined

    :param timestamp: The date string to parse
    :type timestamp: basestring
    :return: A datetime object if a timestamp was specified
    :rtype: datetime.datetime|NoneType
    """
    if timestamp:
        return parse(timestamp)


def _json_file(filename):
    return json.load(argparse.FileType('r')(filename))


def _opt_json_file(filename):
    """Parses a filename as JSON input if defined

    :param filename: The path to the file to parse
    :type filename: basestring
    :return: A decoded JSON object if a filename was specified
    :rtype: dict|list|NoneType
    """
    if filename:
        return _json_file(filename)


def make_naive(value, timezone=None):
    """
    Makes an aware datetime.datetime naive in a given time zone.
    """
    if timezone is None:
        timezone = gettz()
    # If `value` is naive, astimezone() will raise a ValueError,
    # so we don't need to perform a redundant check.
    value = value.astimezone(timezone)
    if hasattr(timezone, 'normalize'):
        # This method is available for pytz time zones.
        value = timezone.normalize(value)
    return value.replace(tzinfo=None)


# noinspection PyPep8Naming
class glucose_momentum_effect(Use):
    """Predict short-term trend of glucose

    """
    @staticmethod
    def configure_app(app, parser):
        parser.add_argument(
            'glucose',
            help='JSON-encoded glucose data file in reverse-chronological order'
        )

        parser.add_argument(
            '--prediction-time',
            type=int,
            nargs=argparse.OPTIONAL,
            help='The total length of forward trend extrapolation in minutes. Defaults to 30.'
        )

        parser.add_argument(
            '--calibrations',
            nargs=argparse.OPTIONAL,
            help='JSON-encoded sensor calibrations data file in reverse-chronological order'
        )

    def get_params(self, args):
        params = super(glucose_momentum_effect, self).get_params(args)

        args_dict = dict(**args.__dict__)

        for key in ('glucose', 'prediction_time', 'calibrations'):
            value = args_dict.get(key)
            if value is not None:
                params[key] = value

        return params

    @staticmethod
    def get_program(params):
        """Parses params into history parser constructor arguments

        :param params:
        :type params: dict
        :return:
        :rtype: tuple(list, dict)
        """
        args = (
            _json_file(params['glucose']),
        )

        kwargs = dict()

        if params.get('prediction_time'):
            kwargs.update(prediction_time=int(params['prediction_time']))

        if params.get('calibrations'):
            kwargs.update(recent_calibrations=_opt_json_file(params['calibrations']) or ())

        return args, kwargs

    def main(self, args, app):
        args, kwargs = self.get_program(self.get_params(args))

        return calculate_momentum_effect(*args, **kwargs)


# noinspection PyPep8Naming
class scheiner_carb_effect(Use):
    """Predict carb effect on glucose, using the Scheiner GI curve

    """
    @staticmethod
    def configure_app(app, parser):
        parser.add_argument(
            'history',
            help='JSON-encoded pump history data file, normalized by openapscontrib.mmhistorytools'
        )

        parser.add_argument(
            '--carb-ratios',
            help='JSON-encoded carb ratio schedule file'
        )

        parser.add_argument(
            '--insulin-sensitivities',
            help='JSON-encoded insulin sensitivities schedule file'
        )

        parser.add_argument(
            '--absorption-time',
            type=int,
            nargs=argparse.OPTIONAL,
            help='The total length of carbohydrate absorption in minutes'
        )

        parser.add_argument(
            '--absorption-delay',
            type=int,
            nargs=argparse.OPTIONAL,
            help='The delay time between a dosing event and when absorption begins'
        )

    def get_params(self, args):
        params = super(scheiner_carb_effect, self).get_params(args)

        args_dict = dict(**args.__dict__)

        for key in ('history', 'carb_ratios', 'insulin_sensitivities', 'absorption_time', 'absorption_delay'):
            value = args_dict.get(key)
            if value is not None:
                params[key] = value

        return params

    @staticmethod
    def get_program(params):
        """Parses params into history parser constructor arguments

        :param params:
        :type params: dict
        :return:
        :rtype: tuple(list, dict)
        """
        args = (
            _json_file(params['history']),
            Schedule(_json_file(params['carb_ratios'])['schedule']),
            Schedule(_json_file(params['insulin_sensitivities'])['sensitivities'])
        )

        kwargs = dict()

        if params.get('absorption_time'):
            kwargs.update(absorption_duration=int(params.get('absorption_time')))

        if params.get('absorption_delay'):
            kwargs.update(absorption_delay=int(params.get('absorption_delay')))

        return args, kwargs

    def main(self, args, app):
        args, kwargs = self.get_program(self.get_params(args))

        return calculate_carb_effect(*args, **kwargs)


# noinspection PyPep8Naming
class scheiner_cob(Use):
    """Predict unabsorbed carbohydrates, using the Scheiner GI curve

    """
    @staticmethod
    def configure_app(app, parser):
        parser.add_argument(
            'history',
            help='JSON-encoded pump history data file, normalized by openapscontrib.mmhistorytools'
        )

        parser.add_argument(
            '--absorption-time',
            type=int,
            nargs=argparse.OPTIONAL,
            help='The total length of carbohydrate absorption in minutes'
        )

        parser.add_argument(
            '--absorption-delay',
            type=int,
            nargs=argparse.OPTIONAL,
            help='The delay time between a dosing event and when absorption begins'
        )

    def get_params(self, args):
        params = super(scheiner_cob, self).get_params(args)

        args_dict = dict(**args.__dict__)

        for key in ('history', 'absorption_time', 'absorption_delay'):
            value = args_dict.get(key)
            if value is not None:
                params[key] = value

        return params

    @staticmethod
    def get_program(params):
        """Parses params into history parser constructor arguments

        :param params:
        :type params: dict
        :return:
        :rtype: tuple(list, dict)
        """
        args = (
            _json_file(params['history']),
        )

        kwargs = dict()

        if params.get('absorption_time'):
            kwargs.update(absorption_duration=int(params.get('absorption_time')))

        if params.get('absorption_delay'):
            kwargs.update(absorption_delay=int(params.get('absorption_delay')))

        return args, kwargs

    def main(self, args, app):
        args, kwargs = self.get_program(self.get_params(args))

        return calculate_cob(*args, **kwargs)


# noinspection PyPep8Naming
class walsh_insulin_effect(Use):
    """Predict insulin effect on glucose, using Walsh's IOB algorithm

    """
    @staticmethod
    def configure_app(app, parser):
        parser.add_argument(
            'history',
            help='JSON-encoded pump history data file, normalized by openapscontrib.mmhistorytools'
        )

        parser.add_argument(
            '--settings',
            nargs=argparse.OPTIONAL,
            help='JSON-encoded pump settings file, optional if --insulin-action-curve is set'
        )

        parser.add_argument(
            '--insulin-action-curve',
            nargs=argparse.OPTIONAL,
            type=float,
            choices=range(3, 7),
            help='Insulin action curve, optional if --settings is set'
        )

        parser.add_argument(
            '--insulin-sensitivities',
            help='JSON-encoded insulin sensitivities schedule file'
        )

        parser.add_argument(
            '--basal-dosing-end',
            nargs=argparse.OPTIONAL,
            help='The timestamp at which temp basal dosing should be assumed to end, '
                 'as a JSON-encoded pump clock file'
        )

        parser.add_argument(
            '--absorption-delay',
            type=int,
            nargs=argparse.OPTIONAL,
            help='The delay time between a dosing event and when absorption begins'
        )

    def get_params(self, args):
        params = super(walsh_insulin_effect, self).get_params(args)

        args_dict = dict(**args.__dict__)

        for key in ('history', 'settings', 'insulin_action_curve', 'insulin_sensitivities', 'basal_dosing_end', 'absorption_delay'):
            value = args_dict.get(key)
            if value is not None:
                params[key] = value

        return params

    @staticmethod
    def get_program(params):
        """Parses params into history parser constructor arguments

        :param params:
        :type params: dict
        :return:
        :rtype: tuple(list, dict)
        """
        args = (
            _json_file(params['history']),
            int(params.get('insulin_action_curve', None) or
                _opt_json_file(params.get('settings', ''))['insulin_action_curve']),
            Schedule(_json_file(params['insulin_sensitivities'])['sensitivities'])
        )

        kwargs = dict(
            basal_dosing_end=_opt_date(_opt_json_file(params.get('basal_dosing_end')))
        )

        if params.get('absorption_delay'):
            kwargs.update(absorption_delay=int(params.get('absorption_delay')))

        return args, kwargs

    def main(self, args, app):
        args, kwargs = self.get_program(self.get_params(args))

        return calculate_insulin_effect(*args, **kwargs)


# noinspection PyPep8Naming
class walsh_iob(Use):
    """Predict IOB using Walsh's algorithm

    """
    @staticmethod
    def configure_app(app, parser):
        parser.add_argument(
            'history',
            help='JSON-encoded pump history data file, normalized by openapscontrib.mmhistorytools'
        )

        parser.add_argument(
            '--settings',
            nargs=argparse.OPTIONAL,
            help='JSON-encoded pump settings file, optional if --insulin-action-curve is set'
        )

        parser.add_argument(
            '--insulin-action-curve',
            nargs=argparse.OPTIONAL,
            type=float,
            choices=range(3, 7),
            help='Insulin action curve, optional if --settings is set'
        )

        parser.add_argument(
            '--basal-dosing-end',
            nargs=argparse.OPTIONAL,
            help='The timestamp at which temp basal dosing should be assumed to end, '
                 'as a JSON-encoded pump clock file'
        )

        parser.add_argument(
            '--absorption-delay',
            type=int,
            nargs=argparse.OPTIONAL,
            help='The delay time between a dosing event and when absorption begins'
        )

        parser.add_argument(
            '--start-at',
            nargs=argparse.OPTIONAL,
            help='File containing the timestamp at which to truncate the beginning of the output, '
                 'as a JSON-encoded ISO date'
        )

        parser.add_argument(
            '--end-at',
            nargs=argparse.OPTIONAL,
            help='File containing the timestamp at which to truncate the end of the output, '
                 'as a JSON-encoded ISO date'
        )

    def get_params(self, args):
        params = super(walsh_iob, self).get_params(args)

        args_dict = dict(**args.__dict__)

        for key in ('history',
                    'settings',
                    'insulin_action_curve',
                    'basal_dosing_end',
                    'absorption_delay',
                    'start_at',
                    'end_at'):
            value = args_dict.get(key)
            if value is not None:
                params[key] = value

        return params

    @staticmethod
    def get_program(params):
        """Parses params into history parser constructor arguments

        :param params:
        :type params: dict
        :return:
        :rtype: tuple(list, dict)
        """
        args = (
            _json_file(params['history']),
            int(params.get('insulin_action_curve', None) or
                _opt_json_file(params.get('settings', ''))['insulin_action_curve'])
        )

        kwargs = dict(
            basal_dosing_end=_opt_date(_opt_json_file(params.get('basal_dosing_end'))),
            start_at=_opt_date(_opt_json_file(params.get('start_at'))),
            end_at=_opt_date(_opt_json_file(params.get('end_at')))
        )

        if params.get('absorption_delay'):
            kwargs.update(absorption_delay=int(params.get('absorption_delay')))

        return args, kwargs

    def main(self, args, app):
        args, kwargs = self.get_program(self.get_params(args))

        return calculate_iob(*args, **kwargs)


# noinspection PyPep8Naming
class glucose_from_effects(Use):
    """Predict glucose from one or more effect schedules

    """
    @staticmethod
    def configure_app(app, parser):
        parser.add_argument(
            'effects',
            nargs=argparse.ONE_OR_MORE,
            help='JSON-encoded effect schedules data files'
        )

        parser.add_argument(
            '--glucose',
            help='JSON-encoded glucose data file in reverse-chronological order'
        )

        parser.add_argument(
            '--momentum',
            help='JSON-encoded momentum effect schedule data file'
        )

    def get_params(self, args):
        params = super(glucose_from_effects, self).get_params(args)

        args_dict = dict(**args.__dict__)

        for key in ('effects', 'glucose', 'momentum'):
            value = args_dict.get(key)
            if value is not None:
                params[key] = value

        return params

    @staticmethod
    def get_program(params):
        """Parses params into history parser constructor arguments

        :param params:
        :type params: dict
        :return:
        :rtype: tuple(list, dict)
        """
        effect_files = params['effects']

        if isinstance(effect_files, str):
            effect_files = ast.literal_eval(effect_files)

        recent_glucose = _json_file(params['glucose'])

        if len(recent_glucose) > 0:
            glucose_file_time = datetime.fromtimestamp(os.path.getmtime(params['glucose']))
            last_glucose_datetime = parse(glucose_data_tuple(recent_glucose[0])[0])

            if last_glucose_datetime.utcoffset() is not None:
                last_glucose_datetime = make_naive(last_glucose_datetime)

            assert abs(glucose_file_time - last_glucose_datetime) < timedelta(minutes=15), \
                'Glucose data is more than 15 minutes old'

        effects = []

        for f in effect_files:
            file_time = datetime.fromtimestamp(os.path.getmtime(f))
            assert datetime.now() - file_time < timedelta(minutes=5), '{} is more than 5 minutes old'.format(f)

            effects.append(_json_file(f))

        args = (effects, recent_glucose)
        kwargs = {}

        momentum_file_name = params.get('momentum')
        if momentum_file_name:
            kwargs['momentum'] = _opt_json_file(params.get('momentum'))
            file_time = datetime.fromtimestamp(os.path.getmtime(params['momentum']))
            assert datetime.now() - file_time < timedelta(minutes=5), '{} is more than 5 minutes old'.format()

        return args, kwargs

    def main(self, args, app):
        args, kwargs = self.get_program(self.get_params(args))

        return calculate_glucose_from_effects(*args, **kwargs)


# noinspection PyPep8Naming
class glucose(Use):
    """Predict glucose. This is a convenience shortcut for insulin and carb effect prediction.

    """
    def configure_app(self, app, parser):
        """Define command arguments.

        Only primitive types should be used here to allow for serialization and partial application
        in via openaps-report.
        """
        parser.add_argument(
            'pump-history',
            help='JSON-encoded pump history data file, normalized by openapscontrib.mmhistorytools'
        )

        parser.add_argument(
            'glucose',
            help='JSON-encoded glucose data file in reverse-chronological order'
        )

        parser.add_argument(
            '--settings',
            nargs=argparse.OPTIONAL,
            help='JSON-encoded pump settings file, optional if --insulin-action-curve is set'
        )

        parser.add_argument(
            '--insulin-action-curve',
            nargs=argparse.OPTIONAL,
            type=float,
            choices=range(3, 7),
            help='Insulin action curve, optional if --settings is set'
        )

        parser.add_argument(
            '--insulin-sensitivities',
            help='JSON-encoded insulin sensitivities schedule file'
        )

        parser.add_argument(
            '--carb-ratios',
            help='JSON-encoded carb ratio schedule file'
        )

        parser.add_argument(
            '--basal-dosing-end',
            nargs=argparse.OPTIONAL,
            help='The timestamp at which temp basal dosing should be assumed to end, '
                 'as a JSON-encoded pump clock file'
        )

    def get_params(self, args):
        params = dict(**args.__dict__)

        if params.get('settings') is None:
            params.pop('settings', None)

        if params.get('insulin_action_curve') is None:
            params.pop('insulin_action_curve', None)

        if params.get('basal_dosing_end') is None:
            params.pop('basal_dosing_end', None)

        params.pop('use', None)
        params.pop('action', None)
        params.pop('report', None)

        return params

    def get_program(self, params):
        """Parses params into history parser constructor arguments

        :param params:
        :type params: dict
        :return:
        :rtype: tuple(list, dict)
        """
        pump_history_file_time = datetime.fromtimestamp(os.path.getmtime(params['pump-history']))
        assert datetime.now() - pump_history_file_time < timedelta(minutes=5), 'History data is more than 5 minutes old'

        recent_glucose = _json_file(params['glucose'])

        if len(recent_glucose) > 0:
            glucose_file_time = datetime.fromtimestamp(os.path.getmtime(params['glucose']))
            last_glucose_datetime = parse(glucose_data_tuple(recent_glucose[0])[0])

            if last_glucose_datetime.utcoffset() is not None:
                last_glucose_datetime = make_naive(last_glucose_datetime)

            assert abs(glucose_file_time - last_glucose_datetime) < timedelta(minutes=15), \
                'Glucose data is more than 15 minutes old'

        args = (
            _json_file(params['pump-history']),
            recent_glucose,
            int(params.get('insulin_action_curve', None) or
                _opt_json_file(params.get('settings', ''))['insulin_action_curve']),
            Schedule(_json_file(params['insulin_sensitivities'])['sensitivities']),
            Schedule(_json_file(params['carb_ratios'])['schedule']),
        )

        return args, dict(basal_dosing_end=_opt_date(_opt_json_file(params.get('basal_dosing_end'))))

    def main(self, args, app):
        args, kwargs = self.get_program(self.get_params(args))

        return future_glucose(*args, **kwargs)
