import wfdb
from xmljson import badgerfish as bf
from xml.etree.ElementTree import fromstring
import numpy as np
import base64
import json
import os

fmts = ['wfdb', 'musexml','json_tnmg', 'leadstudy_xml']


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
    elif format == 'leadstudy_xml':
        return read_leadstudy_xml(path)
    elif format == 'json_tnmg':
        d = read_json_tnmg(path)
        return read_dict_tnmg(d)
    else:
        raise ValueError('Unknown format')


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

def read_leadstudy_xml(file):
    with open(file, 'r', encoding='unicode_escape') as f:
        xml_str = f.read()

    ordered_dict = bf.data(fromstring(xml_str))['CardiologyXML']['StripData']
    sample_rate = ordered_dict['SampleRate']['$']
    print(sample_rate)
    wf = ordered_dict['WaveformData']

    if ordered_dict['Resolution']['@units'] == 'uVperLsb':
        scaling = ordered_dict['Resolution']['$'] / 1000
    else:
        raise ValueError("Invalid Scalling")

    ecg_data = {}
    for lead in wf:
        string_representation = lead['$']
        ecg_data[lead['@lead']] = scaling * np.array([int(n.strip()) for n in string_representation.split(',') if n],
                                                     dtype='<i2')
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


def read_json_tnmg(path_or_content):
    """Read json record"""    
    # Check if 'path' is a string with JSON data or a JSON filename
    if isinstance(path_or_content, str) and os.path.isfile(path_or_content):
        # If it is a string that matches a file, load the data from the JSON file
        with open(path_or_content,'r') as file:
            d = json.load(file)
    else:
        # If it is a string that represents JSON data, load the data directly
        d = json.loads(path_or_content)
    # Return data as a dictionary
    return d


def read_dict_tnmg(d):
    """Read dictionary record"""
    # Read the resolution  
    resolution = d['resolution']
    # Read the sample rate
    sample_rate = d['sampling']
    # Read all available ECG leads and convert them to numpy format
    ecg_np, leads = read_all_leads(d, ['V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'DI', 'DII'])
    # Convert to microvolts measurements
    ecg = convert_to_mv(ecg_np, resolution)
    return ecg, sample_rate, leads
