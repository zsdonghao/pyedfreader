#! /usr/bin/python
# -*- coding: utf8 -*-

#  Open EDF+ file, then save as MAT file
#   Usage:
#     >> python main_load_edf.py >ss3.log 2>ss3.err &
#                                >:Save Log         &:Run on background
#     >> ps   kill   to check and kill process
#
#  Dependencies :
#       dhedfreader.py
#       eegtools > https://github.com/breuderink/eegtools/blob/master/eegtools/io/edfplus.py

__author__ = 'haodong'
__email__ = 'hd311@imperial.ac.uk'

import os
import sys
import argparse
import re
import pprint
import numpy as np
import operator
import dhedfreader      # depend on eegtools
import re
from scipy.io import savemat, loadmat


def print_header_info(h):
    print 'print header info ...'
    # print type(h), h.keys()
    # pprint.pprint(h)
    # print(len(h['label']), len(h['digital_max']), len(h['n_samples_per_record']) )  # 28,28,28
    print 'TABLE of channels & attributes'
    print "record_length: %d seconds\nn_records: %d (total time is record_length*n_records)\nn_channels: %d (EEG,EOG,ECG,EMG,Annotations)\nlocal_subject_id: %s \nlocal_recording_id: %s \ndate_time: %s \ncontiguous: %s \nEDF+: %s" % \
        (h['record_length'], h['n_records'], h['n_channels'], h['local_subject_id'], h['local_recording_id'], h['date_time'], h['contiguous'], h['EDF+'])

    total_time = h['record_length']*h['n_records']
    print "total time calculated by this header > %d seconds = %f hours" % (total_time, float(total_time)/(60*60))

    for i in range(h['n_channels']):
        print i, ' >', h['label'][i], h['units'][i], \
            h['transducer_type'][i], h['prefiltering'][i],\
            h['physical_min'][i], h['physical_max'][i],\
            h['digital_min'][i], h['digital_max'][i], \
            h['n_samples_per_record'][i], h['fs'][i]
# 1  >  EEG T4-CLE      uV      ''                  ''              -998.704       998.7046    -32768.0    32767.0          512
# ^      ^              ^       ^                   ^               ^              ^            ^  ADC 2**16 = 32767 *2     ^
# index  label          units   transducer_type     prefiltering    physical_min/ max           digital_min/ max            n_samples_per_record (No sample rate, sample rate is (n_samples_per_record /record_length)

# record_length: 2 seconds
# n_records: 15277 (total time is record_length*n_records)
# n_channels: 32 (EEG,EOG,ECG,EMG,Annotations)
# local_subject_id: X X X X
# local_recording_id: Startdate X X X X
# date_time: 2000-01-01 22:03:21
# contiguous: True
# EDF+: True

def main(psg_file, ann_file, save_file, saveable = True):
    '''
    Open a EDF+ files (PSG and Annotations) by given the files' paths
    Then save the PSG and Annotations to one .MAT file
    '''
    stage_map = {
    	'W': 0,   # Wake
		'1': 1,   # N1
		'2': 2,   # N2
		'3': 3,   # N3
		'4': 3,   # N4
		'R': 4,   # REM
		'?': 5    # Unknown
	}
    print '\nFile locations ################################################## \n%s\n%s'  % (psg_file, ann_file)
    print '\nReading PSG EDF header ---------------------------------------'
    f = open(psg_file, 'r')
    reader = dhedfreader.BaseEDFReader(f)   # same as reader = eegtools.io.edfplus.BaseEDFReader(f)
    reader.read_header()
    h = reader.header   # h is a dict
    # calculate sample rate of each channel
    h['fs'] = [ a/h['record_length'] for a in h['n_samples_per_record'] ]
    print_header_info(h)
    assert h['contiguous'] == True, 'Don\'t support non-contiguous signals'


    print '\nReading PSG EDF records ---------------------------------------'
    rectime, X, ann_nothing = zip(*reader.records())    # read all data using reader.
    f.close()
    print 'num of time index > %d' % len(rectime)     # rectime = 0 2 4 6 ... with the gap of record_length
    assert len(rectime) == h['n_records'], "num of time index must be equal to num of records "
    assert rectime[1]-rectime[0] == h['record_length'], "gap of time index must be equal to the record length"
    for i in range(len(rectime)-1):
        assert (rectime[i+1] - rectime[i]) == h['record_length'], 'PSG: Record length error, contiguous != True'


    # print '\nParsing PSG EDF signals ---------------------------------------'
    # print 'num of records > %d' % len(X)
    assert len(X) == h['n_records'], "num of records per channel must be equal to num of records."
    # print 'X >',type(X), len(X), type(X[0]), len(X[0]), type(X[0][0]), len(X[0][0])
    #                     15277                  31                      512
    #            tuple   n_records   list    n_channels numpy.ndarray   n_samples_per_record
    #   X[epoch_index][channel_index]



    print '\nReading Ann EDF annotations ---------------------------------------'

    # D 结果正确，速度快的方法！
    f = open(ann_file, 'r')
    reader_ann = dhedfreader.BaseEDFReader(f)
    reader_ann.read_header()
    h_ann = reader_ann.header
    rectime_ann, X_ann, ann = zip(*reader_ann.records())
    f.close()
    for i in range(len(rectime_ann)-1):
        assert (rectime_ann[i+1] - rectime_ann[i]) == h_ann['record_length'], 'Ann: Record length error, contiguous != True'
    # print annotations[0:100]
    # print len(ann), len(rectime)
    # print ann[len(ann)-1]
    # print rectime_ann[0:100]
    # exit()
    time = []
    annotations = []
    # in the file: +410.94106022830.0Sleep stage ?+412.0+412.6870439713.95287322998<Event channel="EEG C3-LER" groupName="EMGArtefact" name=
    # normally : l is a list contains a [(20.9180587558, 30.0, [u'Sleep stage ?'])]
    # For example, '+3456.7892020 R-wave 20 indicates that this data record starts at the occurrence of an R-wave, which is 3456.789s after file start.
    #       see: EDF+ --- Time keeping of data records
    for l in ann:
        if l != []:
            for tup in l:   # but sometime l is a list contains many tuple
                if 'Sleep' in tup[2][0]:
                    # print tup
                    annotations.append(tup[2][0][-1])
                    time.append(tup[0])
                    epoch_duration = tup[1]
                    assert epoch_duration == 20 or 30, 'epoch_duration != 20 or 30'
    for i in range(len(annotations)):
        annotations[i] = stage_map[annotations[i]]
    # print len(annotations)    # SS3_0034  len(annotations)==1022  end with> label:2 time:30922
    print annotations[0:3], annotations[-3:], time[0:3], time[-3:], epoch_duration
    print 'num of timestamps and sleep stage labels > %d' % len(time)
    # exit()
    # end D


    '''
    ＃ C 该方法能的到正确的annotation，但string操作太慢了
    f_ann = open(ann_file, 'r')
    reader_ann = dhedfreader.BaseEDFReader(f_ann)   # same as reader = eegtools.io.edfplus.BaseEDFReader(f)
    reader_ann.read_header()
    f_ann.close()

    stages = []
    offset = 0.0
    count = 0

    annotations = []
    time = []
    with open(ann_file, 'r') as f:
        for line in f:  # only 1 line in the file
            # text = line.strip() # text = +410.941060228 30.0Sleep stage ?+412.0+412.6870439713.95287322998<Event channel="EEG C3-LER" groupName="EMGArtefact" name=
            text = line
            # text = text.replace('+','')
            # print text[1:10000000], type(text)

            for i in range(len(text)):
                if text[i:i+3] == 'Sle':
                    i2 = 0
                    annotations.append(text[i+12])    # the sleep label located at 12:  Sleep stage ?
                    while True:
                        i2 -= 1
                        if text[i+i2] == '+':
                            tmp = text[i+i2+1:i].split('.')
                            time.append(tmp[0])
                            # print text[i+12],tmp
                            break

    # print annotations # print a list will print as ASII
    # for i in range(len(annotations)):   # print one by one will print as Unicode
    #     print annotations[i], time[i]
    print len(annotations)  # SS3_34 1022  end with> 2 30922
    exit()
    # end C
    '''
    '''
    ＃ B 该方法因为 unicode 老变成 \x14 不知道怎么解决，所以我觉得用string操作算了
    with open(ann_file, 'r') as f:
        for line in f:  # only 1 line in the file
            text = text.decode('utf-8')
            # r = re.compile(r"Sleep stage ([?WR1-4]?.{10})", flags=re.UNICODE)   # unicode regex
            # r = re.compile(r"Sleep stage .{10}", re.U)   # unicode regex
            r = re.compile(r"Sleep stage .*\.", flags=re.UNICODE)   # unicode regex
        annotations = r.findall(text)
        print annotations[0:2]
        print len(annotations)  # SS3_0034 is 1022
        exit()
        for ann in annotations:
            ann = ann.split('\x14')
            print ann
        exit()
            # anntotations = pattern.findall(text)

            # print text[1:10000000]

            # annotations = re.findall(u'Sleep stage.{7}', text)
            # annotations = re.findall('Sleep stage [?W1-4R]?.*[0-9]+', text)   # stage W+52 means 52second is Wake
        print annotations, len(annotations)
        exit()
    # end B
    '''


    '''
    # A 该方法在 SS3_0034 中有bug，当sleep stage和signal不对齐时，有误
    with open(ann_file, 'r') as f:
        for line in f:      # only one line
            text = line.strip()
            annotations = re.findall('Sleep stage.{2}', text)   # return ['Sleep stage ?', 'Sleep stage ?'....] without time info


    for idx, ann in enumerate(annotations):
        if 'W' in ann:
            annotations[idx] = stage_map['W']
        elif '1' in ann:
            annotations[idx] = stage_map['1']
        elif '2' in ann:
            annotations[idx] = stage_map['2']
        elif '3' in ann:
            annotations[idx] = stage_map['3']
        elif '4' in ann:
            annotations[idx] = stage_map['4']
        elif 'R' in ann:
            annotations[idx] = stage_map['R']
        elif '?' in ann:
            annotations[idx] = stage_map['?']
        else:
            print 'Unknown ann >',ann
            raise Exception('Unknown annotations string')
    # end A
    '''


    # estimate the epoch duration
    # epoch_duration = round((h['n_records']*h['record_length'])/len(annotations)) # 用方法 D 可以从 EDF 中读取 epoch duration
    print '*** epoch duration = ', epoch_duration
    assert epoch_duration == (30 or 20), 'epoch_duration should be 30 or 20'

    n_epoch = int(h['record_length']*h['n_records']/epoch_duration) # int() round down 向下取整
    total_time = h['record_length']*h['n_records']
    print "*** Total time calculated by PSG header> %d seconds = %f hours" % (total_time, float(total_time)/(60*60))
    print 'num of epoch calculated by PSG>', n_epoch

    h_ann['fs'] = [ a/h_ann['record_length'] for a in h_ann['n_samples_per_record'] ]
    # print_header_info(h_ann)
    print '*** Total time calculated by Ann labels > %f (psg: %d) seconds' % (time[-1], h_ann['record_length']*h_ann['n_records'])
    if time[-1] > h_ann['record_length']*h_ann['n_records']:
        print 'BIGERROR (warning) : time of sleep labels > time of signal'
    print 'num of sleep stages >', len(annotations)

    assert total_time == h_ann['record_length']*h_ann['n_records'], "PSG total time != Ann total time ..."
    # for idx, ann in enumerate(annotations):
    #     print idx
    #     for sub_ann in ann:
    #         if len(sub_ann) > 0:
    #             print sub_ann[2]
    #     print '---\n\n'
    # exit()

    # signals h h_ann
    # annotations
    # print '\nDenoising the Sleep stage using the annotations and timestamp ...'


    print '\nReshaping the signals to %d vectors for %d channels ...' % (len(X[0]),len(X[0]))
    signals = X[0]  # signals[channel_index]     X[epoch_index][channel_index]
    signals = [[] for i in range(len(X[0])) ]
    for r in range(len(X)):   # for each record
        for c in range(len(X[0])):  # for each channel, append signal
            signals[c].extend(X[r][c])  # extend np.array to list
    print 'num of signals: %d, num of samples of channel 0: %d, time duration of channel 0 : %d' \
            % (len(signals), len(signals[0]), len(signals[0])/h['fs'][0])
    assert len(signals[0])/h['fs'][0] == h['record_length'] * h['n_records'], 'Reshaping: length error'
        #   n_channels  total sample in channel 0       total time in seconds
    # print signals[0][0:512] - X[0][0]
    # print signals[0][512:1024] - X[1][0]


    print '\nSaving data into .MAT file ...'
    if saveable == False:
        print '\nsaveable == False, no file saved.'
        return h, h_ann, signals, annotations, time

    # header of PSG
    # scaler
    record_length = h['record_length']; n_records = h['n_records']; n_channels = h['n_channels']
    local_subject_id = h['local_subject_id']; local_recording_id = h['local_recording_id'];
    date_time = h['date_time']; contiguous = h['contiguous']; EDFplus = h['EDF+']
    # list
    label = h['label']; units = h['units']; transducer_type = h['transducer_type']
    prefiltering = h['prefiltering']; physical_min = h['physical_min']; physical_max = h['physical_max']
    digital_min = h['digital_min']; digital_max = h['digital_max']
    n_samples_per_record = h['n_samples_per_record']; fs = h['fs']

    # header of Ann
    # scaler
    record_length_ann = h_ann['record_length']; n_records_ann = h_ann['n_records']; n_channels_ann = h_ann['n_channels']
    local_subject_id_ann = h_ann['local_subject_id']; local_recording_id_ann = h_ann['local_recording_id'];
    date_time_ann = h_ann['date_time']; contiguous_ann = h_ann['contiguous']; EDFplus_ann = h_ann['EDF+']
    # list
    label_ann = h_ann['label']; units_ann = h_ann['units']; transducer_type_ann = h_ann['transducer_type']
    prefiltering_ann = h_ann['prefiltering']; physical_min_ann = h_ann['physical_min']; physical_max_ann = h_ann['physical_max']
    digital_min_ann = h_ann['digital_min']; digital_max_ann = h_ann['digital_max']
    n_samples_per_record_ann = h_ann['n_samples_per_record']; fs_ann = h_ann['fs']

    # save
    savemat( save_file+'.mat', {'signals': signals,\
                                'annotations':annotations, \
                                'time': time,\
                                # header of PSG
                                'record_length' : record_length, \
                                'n_records' : n_records, \
                                'n_channels' : n_channels, \
                                'local_subject_id' : local_subject_id, \
                                'local_recording_id' : local_recording_id, \
                                'date_time' : date_time, \
                                'EDFplus' : EDFplus, \
                                # list
                                'label' : label, \
                                'units' : units, \
                                'transducer_type' : transducer_type, \
                                'prefiltering' : prefiltering, \
                                'physical_min' : physical_min, \
                                'physical_max' : physical_max, \
                                'digital_min' : digital_min, \
                                'digital_max' : digital_max, \
                                'n_samples_per_record' : n_samples_per_record, \
                                'fs' : fs, \
                                # header of Ann
                                'epoch_duration' : epoch_duration, \
                                'record_length_ann' : record_length_ann, \
                                'n_records_ann' : n_records_ann, \
                                'label_ann' : label_ann })

    # # print '\nSaving data into .NPY file ...'
    # np.save( save_file+'.npy', {'signals': signals, 'h':h, 'h_ann':h_ann, 'annotations':annotations})
    print 'Saved >'+os.getcwd()+'/'+save_file

    # Open file using:
    #   MAT > (signals, h, h_ann, annotations) = scipy.io.loadmat('SS1_01.mat')
    #   NPY > (signals, h, h_ann, annotations) = np.load('SS1_01.npy')




if __name__ == '__main__':

    ### Load 1 PSG EDF and 1 Ann EDF
    # psg_dir = '/Users/haodong/Documents/Data/MASS/SS3/'
    # psg_file = psg_dir + '01-03-0034 PSG.edf'
    #
    # ann_dir = '/Users/haodong/Documents/Data/MASS/Annotations/SS3/'
    # ann_file = ann_dir + '01-03-0034 Annotations.edf'
    #
    # save_file = 'SS3_0034'
    #
    # main(psg_file=psg_file, ann_file=ann_file, save_file=save_file, saveable=False)
    # exit()

    # ### Load all PSG EDFs and all Ann EDFs in given files' path
    psg_dir = '/Users/XXX/PSG-Folder/'
    ann_dir = '/Users/XXX/Annotations-Folder/'

    psg_list = os.listdir(psg_dir)
    ann_list = os.listdir(ann_dir)
    print('\nPSG files > %s\n' % psg_list)
    print('Ann files > %s\n' % ann_list)
    for idx, f in enumerate(psg_list):
        if '.edf' not in f:
            psg_list.remove(f)
            print('%d > Remove a non .edf file : %s' % (idx+1,f) )
    for idx, f in enumerate(ann_list):
        if '.edf' not in f:
            ann_list.remove(f)
            print('%d > Remove a non .edf file : %s' % (idx+1,f) )
    assert len(psg_list) == len(ann_list), "num of psg file != num of ann file"

    for i in range(len(psg_list)):
        save_file = 'SS3_'+'%04d' % (i+1)      # SS1_0001
        psg_file = psg_dir + psg_list[i]
        ann_file = ann_dir + ann_list[i]
        main(psg_file=psg_file, ann_file=ann_file, save_file=save_file, saveable=True)
