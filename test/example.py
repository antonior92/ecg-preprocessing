
import argparse
import matplotlib.pyplot as plt
from ecgprep import preprocess, read_ecg
from ecgprep.plot_helpers import get_3by4_format
import ecg_plot
import os
import numpy as np




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot ECG from wfdb')
    parser.add_argument('path', type=str,
                        help='Path to the file to be plot.')
    parser = preprocess.arg_parse_option(parser)
    parser = read_ecg.arg_parse_option(parser)
    args = parser.parse_args(["../ptbxl/00001_hr", "--use_all_leads"])
    print(args)

    ecg, sample_rate, leads = read_ecg.read_ecg(args.path, format='wfdb')
    ecg, sample_rate, leads = preprocess.preprocess_ecg(ecg, sample_rate, leads,
                                                        new_freq=args.new_freq,
                                                        new_len=args.new_len,
                                                        scale=args.scale,
                                                        remove_powerline=args.remove_powerline,
                                                        use_all_leads=args.use_all_leads,
                                                        remove_baseline=args.remove_baseline)


    ecg_plot.plot(ecg_for_plotting, sample_rate=sample_rate, lead_index=leads_for_plotting,
                  columns=4, show_separate_line=False)
    ecg_plot.show()






