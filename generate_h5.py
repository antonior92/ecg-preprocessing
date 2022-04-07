if __name__ == '__main__':
    import preprocess
    import read_ecg
    import argparse
    import h5py
    import pandas as pd
    import tqdm
    import os

    parser = argparse.ArgumentParser(description='Read XML muse and plot the first lead of the obtained ECG. Plot '
                                                 'the first lead and its frequency response.')
    parser.add_argument('input_file', type=str, help='path to RECORDS file.')
    parser.add_argument('out_file', type=str,
                        help='output file containing the plots. ')
    parser.add_argument('--root_dir', type=str,
                        help='The root directory which the relative paths refer to. '
                             'If None just use the folder where `input_file` is.')
    parser = preprocess.arg_parse_option(parser)
    parser = read_ecg.arg_parse_option(parser)
    args = parser.parse_args()
    print(args)

    # open files
    files = pd.read_csv(args.input_file, header=None).values.flatten()
    if args.root_dir is None:
        folder = os.path.dirname(args.input_file)
    else:
        folder = args.root_dir
    n = len(files)  # Get length

    h5f = h5py.File(args.out_file, 'w')
    x = None
    for i, f in enumerate(tqdm.tqdm(files)):
        ecg, sample_rate, leads = read_ecg.read_ecg(os.path.join(folder, f), format=args.fmt)
        ecg_preprocessed, new_rate, new_leads = preprocess.preprocess_ecg(ecg, sample_rate, leads,
                                                                          new_freq=args.new_freq,
                                                                          new_len=args.new_len,
                                                                          scale=args.scale,
                                                                          powerline=args.powerline,
                                                                          use_all_leads=args.use_all_leads,
                                                                          remove_baseline=args.remove_baseline)
        if x is None:
            n_leads, n_samples = ecg_preprocessed.shape
            x = h5f.create_dataset('tracings', (n, n_samples, n_leads), dtype='f8')
        x[i, :, :] = ecg_preprocessed.T

    h5f.close()
