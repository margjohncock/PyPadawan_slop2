"""Summarise measurement means by treatment group."""
import argparse

import pandas as pd


def summarise(input_path, output_path='summary.csv'):
    """Remove missing measurements, average each group, and save a CSV summary."""
    measurements = pd.read_csv(input_path)
    cleaned = measurements.dropna(subset=['value'])
    summary = cleaned.groupby('group')['value'].mean()
    summary.to_csv(output_path)
    return summary


def main():
    """Read terminal options and summarise the selected observations."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='data/measurements.csv', help='Observations CSV with group and value columns')
    parser.add_argument('--output', default='summary.csv', help='Where to save group means')
    args = parser.parse_args()
    summarise(args.input, args.output)


if __name__ == '__main__':
    main()
