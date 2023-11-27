import numpy as np
import scipy.signal as sgn

reduced_leads = ['DI', 'DII', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
all_leads = ['DI', 'DII', 'DIII', 'AVR', 'AVL', 'AVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']


def arg_parse_option(parser, new_len=None, new_freq=None, scale=None):
    """Argparse options for preprocessing"""
    parser.add_argument('--new_freq', type=float, default=None,
                        help='The ECG will be resampled to the provided frequency (in Hz). The standard used is 400Hz.'
                             'Default is None, which does not resample the ECG leads.')
    parser.add_argument('--new_len', type=int, default=None,
                        help='Final length after preprocessing. It will add zero or cut the ECG to get the length.'
                             'The standard used is 4096, a power of two and convenient to work with Convolutional Neural networks.'
                             'Default is None, which does not change the length of the ECG leads.')
    parser.add_argument('--scale', type=float, default=1,
                        help='The ECG will be rescaled by the provided factor.'
                             'Default is 1, which does not rescale the ECG leads.')
    parser.add_argument('--use_all_leads', action='store_true',
                        help="If true compute leads 'DIII', 'AVR', 'AVL', 'AVF' from the remaining ones.")
    parser.add_argument('--remove_baseline', action='store_true',
                        help='If this option, remove baseline by applying high pass filter.')
    parser.add_argument('--remove_powerline', type=float, default=None,
                        help='If included, use notch filter to remove powerline interference (generally being 60Hz).'
                             'Default is None, which does not include the filter.')
    return parser


def remove_baseline_filter(sample_rate):
    fc = 0.8  # [Hz], cutoff frequency
    fst = 0.2  # [Hz], rejection band
    rp = 0.5  # [dB], ripple in passband
    rs = 40  # [dB], attenuation in rejection band
    wn = fc / (sample_rate / 2)
    wst = fst / (sample_rate / 2)

    filterorder, aux = sgn.ellipord(wn, wst, rp, rs)
    sos = sgn.iirfilter(filterorder, wn, rp, rs, btype='high', ftype='ellip', output='sos')
    return sos


def remove_powerline_filter(remove_powerline, sample_rate):
    # Design notch filter
    q = 30.0  # Quality factor
    b, a = sgn.iirnotch(remove_powerline, q, fs=sample_rate)
    return b, a 


def preprocess_ecg(ecg, sample_rate, leads, new_freq=None, new_len=None, scale=1,
                   use_all_leads=False, remove_baseline=False, remove_powerline=None):
    
    # Remove baseline
    if remove_baseline:
        sos = remove_baseline_filter(sample_rate)
        ecg_nobaseline = sgn.sosfiltfilt(sos, ecg, padtype='constant', axis=-1)
    else:
        ecg_nobaseline = ecg

    # Remove powerline
    if remove_powerline is None:
        ecg_nopowerline = ecg_nobaseline
    else:
        b, a = remove_powerline_filter(remove_powerline, sample_rate)
        ecg_nopowerline = sgn.filtfilt(b, a, ecg_nobaseline)

    # Resample
    if new_freq is not None:
        ecg_resampled = sgn.resample_poly(ecg_nopowerline, up=new_freq, down=sample_rate, axis=-1)
    else:
        ecg_resampled = ecg_nopowerline
        new_freq = sample_rate
    n_leads, length = ecg_resampled.shape
    
    # Rescale
    ecg_rescaled = scale*ecg_resampled

    # Add leads if needed
    target_leads = all_leads if use_all_leads else reduced_leads
    n_leads_target = len(target_leads)
    l2p = dict(zip(target_leads, range(n_leads_target)))
    ecg_targetleads = np.zeros([n_leads_target, length])
    for i, l in enumerate(leads):
        if l in target_leads:
            ecg_targetleads[l2p[l], :] = ecg_rescaled[i, :]
    if n_leads_target >= n_leads and use_all_leads:
        ecg_targetleads[l2p['DIII'], :] = ecg_targetleads[l2p['DII'], :] - ecg_targetleads[l2p['DI'], :]
        ecg_targetleads[l2p['AVR'], :] = -(ecg_targetleads[l2p['DI'], :] + ecg_targetleads[l2p['DII'], :]) / 2
        ecg_targetleads[l2p['AVL'], :] = (ecg_targetleads[l2p['DI'], :] - ecg_targetleads[l2p['DIII'], :]) / 2
        ecg_targetleads[l2p['AVF'], :] = (ecg_targetleads[l2p['DII'], :] + ecg_targetleads[l2p['DIII'], :]) / 2

    # Reshape
    if new_len is None or new_len == length:
        ecg_reshaped = ecg_targetleads
    elif new_len > length: # Zero pad
        ecg_reshaped = np.zeros([n_leads_target, new_len])
        pad = (new_len - length) // 2
        ecg_reshaped[..., pad:length+pad] = ecg_targetleads
    else: # cut
        extra = (length - new_len) // 2
        ecg_reshaped = ecg_targetleads[:, extra:new_len + extra]

    return ecg_reshaped, new_freq, target_leads

