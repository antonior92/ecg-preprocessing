import ecg_plot
import argparse
import matplotlib.pyplot as plt
from ecgprep import preprocess, read_ecg, plot_helpers
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot ECG from wfdb')

    parser.add_argument('path', type=str,
                        help='Path to the file to be plot.')
    parser.add_argument('--save', default="",
                        help='Save in the provided path. Otherwise just display image.')
    parser.add_argument('--plot3x4', action='store_true',
                        help='plot 3x4')
    parser.add_argument('--long_leads_3by4', nargs='+',default=['DII'],
                        help='Long leads 3by4')
    parser = preprocess.arg_parse_option(parser)
    parser = read_ecg.arg_parse_option(parser)
    args = parser.parse_args()
    print(args)

    if args.plot3x4 and args.use_all_leads is False:
        args.use_all_leads = True
        print('for 3x4 we always use all leads')

    ecg, sample_rate, leads = read_ecg.read_ecg(args.path, format=args.fmt)
    ecg, sample_rate, leads = preprocess.preprocess_ecg(ecg, sample_rate, leads,
                                                        new_freq=args.new_freq,
                                                        new_len=args.new_len,
                                                        scale=args.scale,
                                                        remove_powerline=args.remove_powerline,
                                                        use_all_leads=args.use_all_leads,
                                                        remove_baseline=args.remove_baseline)

    if args.plot3x4:
        ecg, leads = plot_helpers.get_3by4_format(ecg, leads)
        ecg_plot.plot(ecg, sample_rate=sample_rate,
                      lead_index=leads, style='bw', columns=4)
    else:
        ecg_plot.plot(ecg, sample_rate=sample_rate,
                      lead_index=leads, style='bw', columns=2)



    # rm ticks
    plt.tick_params(
        axis='both',  # changes apply to the x-axis
        which='both',  # both major and minor ticks are affected
        bottom=False,  # ticks along the bottom edge are off
        top=False,  # ticks along the top edge are off
        left=False,
        right=False,
        labelleft=False,
        labelbottom=False)  # labels along the bottom edge are off

    if args.save:
        path, ext = os.path.splitext(args.save)
        if ext == '.png':
            ecg_plot.save_as_png(path)
        elif ext == '.pdf':
            ecg_plot.save_as_pdf(path)
    else:
        ecg_plot.show()
