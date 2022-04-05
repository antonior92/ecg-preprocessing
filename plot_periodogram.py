import ecg_plot
import argparse
import matplotlib.pyplot as plt
import preprocess
import os
import read_ecg
import scipy.signal as sgn


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot ECG from wfdb')

    parser.add_argument('path', type=str,
                        help='Path to the file to be plot.')
    parser.add_argument('--save', default="",
                        help='Save in the provided path. Otherwise just display image.')
    parser = preprocess.arg_parse_option(parser)
    parser = read_ecg.arg_parse_option(parser)
    args = parser.parse_args()
    print(args)

    ecg, sample_rate, leads = read_ecg.read_ecg(args.path, format=args.fmt)
    ecg, sample_rate, leads = preprocess.preprocess_ecg(ecg, sample_rate, leads,
                                                        new_freq=args.new_freq,
                                                        new_len=args.new_len,
                                                        scale=args.scale,
                                                        powerline=args.powerline,
                                                        use_all_leads=args.use_all_leads,
                                                        remove_baseline=args.remove_baseline)

    freq, Pxx = sgn.welch(ecg[0], sample_rate, window='hamming', nperseg=2500, nfft=10000, scaling='density')

    fig, ax = plt.subplots(ncols=2)
    ax[0].plot(freq, Pxx)
    ax[0].grid()
    ax[0].set_title("Linear scale")
    ax[0].set_ylabel("Power Spectral Density (mV$^2/$Hz)")
    ax[0].set_xlabel("Frequency (Hz)")
    ax[0].set_xlim([0, 60])
    ax[1].grid()
    ax[1].plot(freq, Pxx)
    ax[1].axvline(sample_rate/2, color='black', ls='--')
    ax[1].set_title("Log scale")
    ax[1].set_xlabel("Frequency (Hz)")
    ax[1].set_yscale('log')
    ax[1].set_xlim([0, 250])
    ax[1].set_ylim([1e-9, 1e-1])
    plt.suptitle('Welch Periodogram')
    plt.tight_layout()
    if args.save:
        plt.savefig(args.save)
    else:
        plt.show()