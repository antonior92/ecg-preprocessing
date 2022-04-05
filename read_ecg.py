import wfdb
from xmljson import badgerfish as bf
from xml.etree.ElementTree import fromstring
import numpy as np
import base64

fmts = ['wfdb', 'musexml']


def arg_parse_option(parser):
    """Argparse options for read ecg"""
    parser.add_argument('--fmt', choices=fmts, default='wfdb',
                        help='format used.')
    return parser


def read_ecg(path, format='wfdb'):
    """Read ECG record"""
    if format == 'wfdb':
        return read_wfdb(path)
    elif format == 'musexml':
        return read_musexml(path)
    else:
        raise ValueError('Unknow format')


def read_wfdb(path):
    """Read wfdb record"""
    record = wfdb.rdrecord(path)
    return record.p_signal.T, record.fs, record.sig_name


def read_musexml(file):
    """Read ge musexml record"""
    with open(file, 'r') as f:
        xml_str = f.read()

    ordered_dict = bf.data(fromstring(xml_str))
    wf = ordered_dict['RestingECG']['Waveform'][1]
    sample_rate = wf['SampleBase']['$']

    ecg_data = {}
    for lead in wf['LeadData']:
        scaling = float(lead['LeadAmplitudeUnitsPerBit']['$'].replace(',', '.'))
        unit = lead['LeadAmplitudeUnits']['$'].lower()

        if unit == 'microvolts':
           scaling = scaling / 1000
        elif unit == 'millivolts':
            pass
        else:
            raise ValueError('LeadAmplitudeUnit = {} unnacaouted for'.format(unit))

        lead_string = ''.join(lead['WaveFormData']['$'].split('\n'))
        lead_data_bytes = base64.b64decode(lead_string)
        lead_data = np.frombuffer(lead_data_bytes, dtype='i2') * scaling

        ecg_data[lead['LeadID']['$']] = lead_data
    # Stack data and return numpy array
    ecg = np.stack(list(ecg_data.values()), axis=0)
    leads = []
    for l in ecg_data.keys():
        if l in ["I", "II", "III"]:
            leads.append("D" + l)
        else:
            leads.append(l)
    return ecg, sample_rate, leads