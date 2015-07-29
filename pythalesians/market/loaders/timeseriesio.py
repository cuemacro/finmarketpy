__author__ = 'saeedamen' # Saeed Amen / saeed@thalesians.com

#
# Copyright 2015 Thalesians Ltd. - http//www.thalesians.com / @thalesians
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and limitations under the License.
#

"""
TimeSeriesIO

Write and reads time series data to disk in various formats, CSV and HDF5 format.

"""

import pandas
import codecs
import datetime
from dateutil.parser import parse
import shutil

from openpyxl import load_workbook
import os.path

from pythalesians.util.constants import Constants
from pythalesians.util.loggermanager import LoggerManager

class TimeSeriesIO:

    def __init__(self):
        self.logger = LoggerManager().getLogger(__name__)

    ### functions to handle Excel on disk
    def write_time_series_to_excel(self, fname, sheet, data_frame, create_new=False):
        """
        write_time_series_to_excel - writes Pandas data frame to disk in Excel format

        Parameters
        ----------
        fname : str
            Excel filename to be written to
        sheet : str
            sheet in excel
        data_frame : DataFrame
            data frame to be written
        create_new : boolean
            to create a new Excel file
        """

        if(create_new):
            writer = pandas.ExcelWriter(fname, engine='xlsxwriter')
        else:
            if os.path.isfile(fname):
                book = load_workbook(fname)
                writer = pandas.ExcelWriter(fname, engine='xlsxwriter')
                writer.book = book
                writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
            else:
                writer = pandas.ExcelWriter(fname, engine='xlsxwriter')

        data_frame.to_excel(writer, sheet_name=sheet, engine='xlsxwriter')

        writer.save()
        writer.close()

    def write_time_series_to_excel_writer(self, writer, sheet, data_frame):
        """
        write_time_series_to_excel_writer - writes Pandas data frame to disk in Excel format for a writer

        Parameters
        ----------
        writer : ExcelWriter
            File handle to use for writing Excel file to disk
        sheet : str
            sheet in excel
        data_frame : DataFrame
            data frame to be written
        """
        data_frame.to_excel(writer, sheet, engine='xlsxwriter')

    def read_excel_data_frame(self, f_name, excel_sheet, freq, cutoff = None, dateparse = None,
                            postfix = '.close', intraday_tz = 'UTC'):
        """
        read_excel_data_frame - Reads Excel from disk into DataFrame

        Parameters
        ----------
        f_name : str
            Excel file path to read
        freq : str
            Frequency of data to read (intraday/daily etc)
        cutoff : DateTime (optional)
            end date to read up to
        dateparse : str (optional)
            date parser to use
        postfix : str (optional)
            postfix to add to each columns
        intraday_tz : str
            timezone of file if uses intraday data

        Returns
        -------
        DataFrame
        """

        return self.read_csv_data_frame(f_name, freq, cutoff = cutoff, dateparse = dateparse,
                            postfix = postfix, intraday_tz = intraday_tz, excel_sheet = excel_sheet)

    ### functions to handle HDF5 on disk
    def write_time_series_cache_to_disk(self, fname, data_frame):
        """
        write_time_series_cache_to_disk - writes Pandas data frame to disk as HDF5 format

        Parmeters
        ---------
        fname : str
            path of file
        data_frame : DataFrame
            data frame to be written to disk
        """

        store = pandas.HDFStore(self.get_h5_filename(fname), complib="blosc", complevel=9)

        if ('intraday' in fname):
            data_frame = data_frame.astype('float32')

        store['data'] = data_frame
        store.close()

    def get_h5_filename(self, fname):
        """
        get_h5_filename - Strips h5 off filename returning first portion of filename

        Parameters
        ----------
        fname : str
            h5 filename to strip

        Returns
        -------
        str
        """
        if fname[-3:] == '.h5':
            return fname

        return fname + ".h5"

    def write_r_compatible_hdf_dataframe(self, data_frame, fname, fields = None):
        """
        write_r_compatible_hdf_dataframe - Write a DataFrame to disk in as an R compatible HDF5 file

        Parameters
        ----------
        data_frame : DataFrame
            data frame to be written
        fname : str
            file path to be written
        fields : list(str)
            columns to be written
        """
        fname_r = self.get_h5_filename(fname)

        self.logger.info("About to dump R binary HDF5 - " + fname_r)
        data_frame32 = data_frame.astype('float32')

        if fields is None:
            fields = data_frame32.columns.values

        # decompose date/time into individual fields (easier to pick up in R)
        data_frame32['Year'] = data_frame.index.year
        data_frame32['Month'] = data_frame.index.month
        data_frame32['Day'] = data_frame.index.day
        data_frame32['Hour'] = data_frame.index.hour
        data_frame32['Minute'] = data_frame.index.minute
        data_frame32['Second'] = data_frame.index.second
        data_frame32['Millisecond'] = data_frame.index.microsecond / 1000

        data_frame32 = data_frame32[
            ['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second', 'Millisecond'] + fields]

        cols = data_frame32.columns

        store_export = pandas.HDFStore(fname_r)
        store_export.put('df_for_r', data_frame32, data_columns=cols)
        store_export.close()

    def read_time_series_cache_from_disk(self, fname):
        """
        read_time_series_cache_from_disk - Reads time series cache from disk

        Parameters
        ----------
        fname : str
            file to be read from

        Returns
        -------
        DataFrame
        """

        if os.path.isfile(self.get_h5_filename(fname)):
            store = pandas.HDFStore(self.get_h5_filename(fname))
            data_frame = store.select("data")

            if ('intraday' in fname):
                data_frame = data_frame.astype('float32')

            store.close()

            return data_frame

        return None

    ### functions for CSV reading and writing
    def write_time_series_to_csv(self, csv_path, data_frame):
        data_frame.to_csv(csv_path)

    def read_csv_data_frame(self, f_name, freq, cutoff = None, dateparse = None,
                            postfix = '.close', intraday_tz = 'UTC', excel_sheet = None):
        """
        read_csv_data_frame - Reads CSV/Excel from disk into DataFrame

        Parameters
        ----------
        f_name : str
            CSV/Excel file path to read
        freq : str
            Frequency of data to read (intraday/daily etc)
        cutoff : DateTime (optional)
            end date to read up to
        dateparse : str (optional)
            date parser to use
        postfix : str (optional)
            postfix to add to each columns
        intraday_tz : str (optional)
            timezone of file if uses intraday data
        excel_sheet : str (optional)
            Excel sheet to be read

        Returns
        -------
        DataFrame
        """

        if(freq == 'intraday'):

            if dateparse is None:
                dateparse = lambda x: datetime.datetime(*map(int, [x[6:10], x[3:5], x[0:2],
                                                   x[11:13], x[14:16], x[17:19]]))
            elif dateparse is 'dukascopy':
                dateparse = lambda x: datetime.datetime(*map(int, [x[0:4], x[5:7], x[8:10],
                                                   x[11:13], x[14:16], x[17:19]]))
            elif dateparse is 'c':
                # use C library for parsing dates, several hundred times quicker
                # requires compilation of library to install
                import ciso8601
                dateparse = lambda x: ciso8601.parse_datetime(x)

            if excel_sheet is None:
                data_frame = pandas.read_csv(f_name, index_col = 0, parse_dates = True, date_parser = dateparse)
            else:
                data_frame = pandas.read_excel(f_name, excel_sheet, index_col = 0, na_values=['NA'])

            data_frame = data_frame.astype('float32')
            data_frame.index.names = ['Date']

            old_cols = data_frame.columns
            new_cols = []

            # add '.close' to each column name
            for col in old_cols:
                new_cols.append(col + postfix)

            data_frame.columns = new_cols
        else:
            # daily data
            if 'events' in f_name:

                data_frame = pandas.read_csv(f_name)

                # very slow conversion
                data_frame = data_frame.convert_objects(convert_dates = 'coerce')

            else:
                if excel_sheet is None:
                    data_frame = pandas.read_csv(f_name, index_col=0, parse_dates =["DATE"], date_parser = dateparse)
                else:
                    data_frame = pandas.read_excel(f_name, excel_sheet, index_col = 0, na_values=['NA'])

        # convert Date to Python datetime
        # datetime data_frame['Date1'] = data_frame.index

        # slower method: lambda x: pandas.datetime.strptime(x, '%d/%m/%Y %H:%M:%S')
        # data_frame['Date1'].apply(lambda x: datetime.datetime(int(x[6:10]), int(x[3:5]), int(x[0:2]),
        #                                        int(x[12:13]), int(x[15:16]), int(x[18:19])))

        # data_frame.index = data_frame['Date1']
        # data_frame.drop('Date1')

        # slower method: data_frame.index = pandas.to_datetime(data_frame.index)

        if(freq == 'intraday'):
            # assume time series are already in UTC and assign this (can specify other time zones)
            data_frame = data_frame.tz_localize(intraday_tz)

        # end cutoff date
        if cutoff is not None:
            if (isinstance(cutoff, str)):
                cutoff = parse(cutoff)

            data_frame = data_frame.loc[data_frame.index < cutoff]

        return data_frame

    def convert_csv_data_frame(self, f_name, category, freq, cutoff=None, dateparse=None):
        """
        convert_csv_data_frame - Converts CSV file to HDF5 file

        Parameters
        ----------
        f_name : str
            File name to be read
        category : str
            data category of file (used in HDF5 filename)
        freq : str
            intraday/daily frequency (used in HDF5 filename)
        cutoff : DateTime (optional)
            filter dates up to here
        dateparse : str
            date parser to use
        """

        self.logger.info("About to read... " + f_name)

        data_frame = self.read_csv_data_frame(f_name, freq, cutoff=cutoff, dateparse=dateparse)

        category_f_name = self.create_cache_file_name(category)

        self.write_time_series_cache_to_disk(
            category_f_name, data_frame)

    def clean_csv_file(self, f_name):
        """
        clean_csv_file - Cleans up CSV file (removing empty characters) before writing back to disk

        Parameters
        ----------
        f_name : str
            CSV file to be cleaned
        """

        with codecs.open (f_name, 'rb', 'utf-8') as myfile:
            data = myfile.read()

            # clean file first if dirty
            if data.count( '\x00' ):
                self.logger.info('Cleaning CSV...')

                with codecs.open(f_name + '.tmp', 'w', 'utf-8') as of:
                    of.write(data.replace('\x00', ''))

                shutil.move(f_name + '.tmp', f_name)

    def create_cache_file_name(self, filename):
        return Constants().folder_time_series_data + "/" + filename
