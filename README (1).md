# Group measurement summary

Summarise repeated measurements by treatment group to compare average values.

## Method

Read observations, remove rows with missing values, group by treatment and calculate the mean measurement.

## Input data

Use `data/measurements.csv`. Each row is one observation. `group` is the treatment label and `value` is a measurement in millimetres. Keep the column names unchanged.

## Run the example

Use Python 3.11 or newer. Run these commands from this project folder:

```bash
python -m pip install -r requirements.txt
python analysis.py --input data/measurements.csv --output summary.csv
```

## Expected output

The program writes `summary.csv`. The example contains three observations: group A has mean 3.0 and group B has mean 8.0. Compare these values with your output.

## Settings

`--input` chooses the observations file; `--output` chooses where to save the summary. The default paths are `data/measurements.csv` and `summary.csv`.
