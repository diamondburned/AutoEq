import os
import sys
from pathlib import Path
ROOT_PATH = Path(__file__).resolve().parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(1, str(ROOT_PATH))
import numpy as np
import re
from frequency_response import FrequencyResponse
from biquad import peaking, low_shelf, high_shelf, digital_coeffs
from argparse import ArgumentParser, SUPPRESS

fns = {'PK': peaking, 'LS': low_shelf, 'HS': high_shelf}
fs = 48000


def peq2fr(fc, q, gain, filts):
    if type(fc) in [float, int]:
        fc = np.array([fc])
    if type(q) in [float, int]:
        q = np.array([q])
    if type(gain) in [float, int]:
        gain = np.array([gain])
    if type(filts) == str:
        filts = [filts] * len(fc)
    fr = FrequencyResponse(name='PEG')
    c = np.zeros(fr.frequency.shape)
    for i, filt in enumerate(filts):
        a0, a1, a2, b0, b1, b2 = fns[filt](fc[i], q[i], gain[i], fs=fs)
        c += digital_coeffs(fr.frequency, fs, a0, a1, a2, b0, b1, b2)
    fr.raw = c
    return fr


def peq2geq(fc, q, gain, filts, normalize=False):
    fr = peq2fr(fc, q, gain, filts)
    fr.equalization = fr.raw
    return fr.eqapo_graphic_eq(normalize=normalize)


def read_eqapo(file_path):
    with open(file_path) as fh:
        lines = fh.read().strip().split('\n')
    fcs = []
    qs = []
    gains = []
    filts = []
    for line in lines:
        if line[0] == '#':  # Comment line
            continue
        tokens = line.split()
        if tokens[0] == 'Filter:':
            fcs.append(float(tokens[tokens.index('Fc') + 1]))
            qs.append(float(tokens[tokens.index('Q') + 1]))
            gains.append(float(tokens[tokens.index('Gain') + 1]))
            filts.append(re.search(r'(PK|LS|HS)', line)[0])
        else:
            print(f'Unsupported EqualizerAPO control type "{line}"')
    return fcs, qs, gains, filts


def main():
    parser = ArgumentParser()
    parser.add_argument('--fc', type=float, nargs='+', help='Center frequencies in Hz')
    parser.add_argument('--q', type=float, nargs='+', help='Qualities')
    parser.add_argument('--gain', type=float, nargs='+', help='Gains')
    parser.add_argument('--type', nargs='+',
                        help='Filter types. "PK" for peaking, LS for low-shelf and HS for high-shelf')
    parser.add_argument('--file', type=str, default=SUPPRESS, help='Path to EqualizerAPO config file')
    parser.add_argument('--normalize', action='store_true', help='Normalize gain?')
    args = parser.parse_args()
    if args.file:
        print(peq2geq(*read_eqapo(args.file)))
    else:
        print(peq2geq(args.fc, args.q, args.gain, args.type, normalize=args.normalize))


if __name__ == '__main__':
    main()
