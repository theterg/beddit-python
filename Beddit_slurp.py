#!/usr/bin/env python

import argparse
from Beddit import *
import datetime
import logging
import sys
import os
import pickle


def _get_date(date_string):
    return datetime.datetime.strptime(date_string, '%Y-%m-%d').date()


def write_pickle(filename, data):
    f = open(filename, 'wb')
    pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
    f.close()


def main():
    parser = argparse.ArgumentParser('Retrieve data from a Beddit acct')
    parser.add_argument('--username', required=True, type=str,
                        help='Beddit account username')
    parser.add_argument('--password', required=True, type=str,
                        help='Beddit account password')
    parser.add_argument('--from_date', type=_get_date,
                        default=datetime.date(2000, 1, 1),
                        help='date to fetch YYYY-MM-DD')
    parser.add_argument('--to_date', type=_get_date,
                        default=datetime.date.today(),
                        help='date to fetch YYYY-MM-DD default is from_date))')
    parser.add_argument('--overwrite_files', default=False,
                        action='store_true',
                        help='Overwrite files already fetched')
    parser.add_argument('--raw_signal_data', default=False,
                        action='store_true',
                        help='Retrieve raw BCG data (large dataset!)' +
                             'Use with care, avoid overloading API')
    parser.add_argument('--as_user', type=str, default=False,
                        help='If multiple users are linked to this account, ' +
                             'use this username to retrieve data')
    parser.add_argument('--format', type=str, default='pk',
                        help='Output file format')
    parser.add_argument('--destination', type=str, default='results/',
                        help='Output file directory, defaults to results/')
    parser.add_argument('--debug', default=False, action='store_true',
                        help='Turn on connection debugging')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    writer = False
    if args.format == 'pk':
        writer = write_pickle
    else:
        logging.error('Unsupported file extension '+args.format)
        return 1

    b = Beddit(args.username, args.password)
    if not b.login():
        logging.error('Unable to log into beddit account')
        return 1

    nights = b.getNights(startDate=args.from_date,
                         endDate=args.to_date,
                         username=args.as_user)
    if len(nights) == 0:
        logging.error('No sleep data found within given range')
        return 1

    if not os.path.exists(args.destination):
        os.mkdir(args.destination)

    logging.info(str(len(nights))+' nights found, starting data retrieval')
    for night in nights:
        filename = args.destination+'bedditdata_'+night['date']+'.'+args.format
        if os.path.exists(filename) and not args.overwrite_files:
            logging.warn('Filename '+filename+' already exists, skipping')
            continue
        logging.info('retrieving data from '+night['date'])
        date = datetime.datetime.strptime(night['date'], "%Y-%m-%d")
        info = b.getDetailedInfo(date=date, username=args.as_user, numpy=True)
        results = b.getResults(date=date, username=args.as_user, numpy=True)
        info.update(results)
        if args.raw_signal_data:
            signal = b.getSignal(date=date, username=args.as_user, numpy=True)
            info.update(signal)
        writer(filename, info)
        logging.debug(filename+' written')
        return 0    # Remove me to actually retrieve all the data
    return 0

if __name__ == '__main__':
    sys.exit(main())
