# predict
An [openaps](https://github.com/openaps/openaps) plugin for predicting glucose trends from historical input

[![Build Status](https://travis-ci.org/loudnate/openaps-predict.svg)](https://travis-ci.org/loudnate/openaps-predict)

## Disclaimer
This tool is highly experimental and intended for education, not intended for therapy.

## Getting started
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
  -h, --help  show this help message and exit

## Device predict:
  vendor openapscontrib.predict
  
  predict - tools for predicting glucose trends
  
  
  
      

  USAGE       Usage Details
    glucose   Predict glucose
```

Use the command help menu to see available arguments.
```bash
$ openaps use predict glucose -h
usage: openaps-use predict glucose [-h] [--settings [SETTINGS]]
                                   [--insulin-action-curve [{3,4,5,6}]]
                                   [--insulin-sensitivities INSULIN_SENSITIVITIES]
                                   [--carb-ratios CARB_RATIOS]
                                   [--basal-dosing-end [BASAL_DOSING_END]]
                                   normalized-history normalized-glucose

Predict glucose

positional arguments:
  pump-history          JSON-encoded pump history data file, normalized by
                        openapscontrib.mmhistorytools
  glucose               JSON-encoded glucose data file in 
                        reverse-chronological order

optional arguments:
  -h, --help            show this help message and exit
  --settings [SETTINGS]
                        JSON-encoded pump settings file, optional if --idur is
                        set
  --insulin-action-curve [{3,4,5,6}], --idur [{3,4,5,6}]
                        Insulin action curve, optional if --settings is set
  --insulin-sensitivities INSULIN_SENSITIVITIES, --sensf INSULIN_SENSITIVITIES
                        JSON-encoded insulin sensitivities schedule file
  --carb-ratios CARB_RATIOS, --cratio CARB_RATIOS
                        JSON-encoded carb ratio schedule file
  --basal-dosing-end [BASAL_DOSING_END]
                        The timestamp at which temp basal dosing should be
                        assumed to end, as a JSON-encoded pump clock file
```

## Examples

Add a report flow to predict future glucose from pump history, with and without future basal dosing:
```
$ openaps report add predict_glucose.json JSON predict glucose \ 
        normalize_history.json \
		recent_glucose.json \
		--settings read_settings.json \
		--insulin-sensitivities read_insulin_sensitivies.json \
		--carb-ratios read_carb_ratios.json

$ openaps report add predict_glucose_without_future_basal.json JSON predict glucose \ 
        normalize_history.json \
		recent_glucose.json \
		--settings read_settings.json \
		--insulin-sensitivities read_insulin_sensitivies.json \
		--carb-ratios read_carb_ratios.json
		--basal-dosing-end read_clock.json
```

## Contributing
Contributions are welcome and encouraged in the form of bugs and pull requests.

### Testing
 
Unit tests can be run manually via setuptools. This is also handled by TravisCI after opening a pull request.
 
```bash
$ python setup.py test
```
