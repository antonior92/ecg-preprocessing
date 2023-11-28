import wfdb
from xmljson import badgerfish as bf
from xml.etree.ElementTree import fromstring
import numpy as np
import base64
import json
import os

fmts = ['wfdb', 'musexml','json_tnmg']

def arg_parse_option(parser):
    """Argparse options for read ecg"""
    parser.add_argument('--fmt', choices=fmts, default='wfdb',
                        help='format used.')    
    return parser


def read_ecg(path, format='wfdb'):
    """Read ECG record from file path"""
    if format == 'wfdb':
        # Load data from WFDB file
        return read_wfdb(path)
    elif format == 'musexml':
        # Load data from XML file
        with open(path, 'r') as f:
            xml_str = f.read()
        return read_musexml(xml_str)
    elif format == 'json_tnmg':  
        # Load data from JSON file
        with open(path,'r') as file:
            d = json.load(file)
        return read_dict_tnmg(d)
    else:
        raise ValueError('Unknown format')


def read_ecg_string(str_content, format='json_tnmg'):
    """Read ECG record from data string"""
    if format == 'wfdb':
        raise ValueError('wfdb format is not supported for strings')
    elif format == 'musexml':
        # Load data directly from XML string
        return read_musexml(str_content)
    elif format == 'json_tnmg':
        # Load data directly from JSON string
        d = json.loads(str_content)
        return read_dict_tnmg(d)
    else:
        raise ValueError('Unknown format')


def read_wfdb(path):
    """Read wfdb record"""
    record = wfdb.rdrecord(path)
    return record.p_signal.T, record.fs, record.sig_name


def read_musexml(xml_str):
    """Read ge musexml record"""    
    ordered_dict = bf.data(fromstring(xml_str))
    wf = ordered_dict['RestingECG']['Waveform'][1]
    sample_rate = wf['SampleBase']['$']

    ecg_data = {}
    for lead in wf['LeadData']:
        if isinstance(lead['LeadAmplitudeUnitsPerBit']['$'], str):
            scaling = float(lead['LeadAmplitudeUnitsPerBit']['$'].replace(',', '.'))
        else:
            scaling = float(lead['LeadAmplitudeUnitsPerBit']['$'])
        unit = lead['LeadAmplitudeUnits']['$'].lower()

        if unit == 'microvolts':
           scaling = scaling / 1000
        elif unit == 'millivolts':
            pass
        else:
            raise ValueError('LeadAmplitudeUnit = {} unaccounted for.'.format(unit))

        lead_string = ''.join(lead['WaveFormData']['$'].split('\n'))
        lead_data_bytes = base64.b64decode(lead_string)
        lead_data = np.frombuffer(lead_data_bytes, dtype='i2')*scaling

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


def read_lead(string_representation):
    return np.array([int(n) for n in string_representation.split(';') if n], dtype='<i2')


def read_all_leads(c, leads):
    l1 = read_lead(c[leads[0]])
    n = len(l1)
    ecg = np.zeros((len(leads), n), dtype='<i2')
    ecg[0, :] = l1
    leads_available = []
    leads_available.append(leads[0])
    for i, l in enumerate(leads[1:]):
        try:
            ecg[i+1, :] = read_lead(c[l])
            leads_available.append(l)
        except:
            print('{} missing'.format(l))
    return ecg, leads_available


def convert_to_mv(x, resolution):
    return x / 1000 * resolution


def read_dict_tnmg(d):
    """Read dictionary record"""
    # Read the resolution  
    resolution = d['resolution']
    # Read the sample rate
    try:
        sample_rate = d['sample_rate']
    except:
        sample_rate = d['sampling']
    # Read all available ECG leads and convert them to numpy format
    ecg_np, leads = read_all_leads(d, ['DI', 'DII', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6'])
    # Convert to microvolts measurements
    ecg = convert_to_mv(ecg_np, resolution)
    return ecg, sample_rate, leads
