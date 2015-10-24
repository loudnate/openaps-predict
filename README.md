# predict
An [openaps](https://github.com/openaps/openaps) plugin for predicting glucose effects and trends from historical input

[![Build Status](https://travis-ci.org/loudnate/openaps-predict.svg)](https://travis-ci.org/loudnate/openaps-predict)

## Disclaimer
This tool is highly experimental and intended for education, not intended for therapy.

## Getting started
### Installing from pypi

```bash
$ sudo easy_install openapscontrib.predict
```
### Installing from source for development
Clone the repository and link via setuptools:
```bash
$ python setup.py develop
```

### Adding to your openaps project
```bash
$ openaps vendor add openapscontrib.predict
$ openaps device add predict predict
```

## Usage
Use the device help menu to see available commands.
```bash
$ openaps use predict -h
usage: openaps-use predict [-h] USAGE ...

optional arguments:
  -h, --help            show this help message and exit

## Device predict:
  vendor openapscontrib.predict

  predict - tools for predicting glucose trends





  USAGE                 Usage Details
    glucose             Predict glucose. This is a convenience shortcut for
                        insulin and carb effect prediction.
    glucose_from_effects
                        Predict glucose from one or more effect schedules
    scheiner_carb_effect
                        Predict carb effect on glucose, using the Scheiner GI
                        curve
    walsh_insulin_effect
                        Predict insulin effect on glucose, using Walsh's IOB
                        algorithm
    walsh_iob           Predict IOB using Walsh's algorithm
```

Use the command help menu to see available arguments.
```bash
usage: openaps-use predict glucose [-h] [--settings [SETTINGS]]
                                   [--insulin-action-curve [{3,4,5,6}]]
                                   [--insulin-sensitivities INSULIN_SENSITIVITIES]
                                   [--carb-ratios CARB_RATIOS]
                                   [--basal-dosing-end [BASAL_DOSING_END]]
                                   pump-history glucose

Predict glucose. This is a convenience shortcut for insulin and carb effect prediction.

positional arguments:
  pump-history          JSON-encoded pump history data file, normalized by
                        openapscontrib.mmhistorytools
  glucose               JSON-encoded glucose data file in reverse-
                        chronological order

optional arguments:
  -h, --help            show this help message and exit
  --settings [SETTINGS]
                        JSON-encoded pump settings file, optional if
                        --insulin-action-curve is set
  --insulin-action-curve [{3,4,5,6}]
                        Insulin action curve, optional if --settings is set
  --insulin-sensitivities INSULIN_SENSITIVITIES
                        JSON-encoded insulin sensitivities schedule file
  --carb-ratios CARB_RATIOS
                        JSON-encoded carb ratio schedule file
  --basal-dosing-end [BASAL_DOSING_END]
                        The timestamp at which temp basal dosing should be
                        assumed to end, as a JSON-encoded pump clock file
```

## Examples

Add a report flow to predict future glucose from pump history:
```
$ openaps report add insulin_effect_without_future_basal.json JSON predict walsh_insulin_effect \
        normalize_history.json \
		--settings read_settings.json \
		--insulin-sensitivities read_insulin_sensitivies.json \
		--basal-dosing-end read_clock.json

$ openaps report add carb_effect.json JSON predict scheiner_carb_effect \
        normalize_history.json \
		--carb-ratios read_carb_ratios.json
		--insulin-sensitivities read_insulin_sensitivies.json

$ openaps report add predict_glucose_without_future_basal JSON predict glucose_from_effects \
        insulin_effect_without_future_basal.json \
        carb_effect.json \
        --glucose clean_glucose.json
```

## Contributing
Contributions are welcome and encouraged in the form of bugs and pull requests.

### Testing

Unit tests can be run manually via setuptools. This is also handled by TravisCI after opening a pull request.

```bash
$ python setup.py test
```
