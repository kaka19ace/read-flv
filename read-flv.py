#!/usr/bin/env python
#  Copyright (c) 2014 Zhong Kaixiang
#
#  This file is simple parser for flv file 
#

import sys, os
fname = sys.argv[1]
file_size = os.path.getsize(fname)

f = open(fname, "r")
if file_size <= 11:
    print "file not match our require"
    sys.exit(1)

'''
flv is big-endian 
'''

def str2hex(s):
    return ':'.join(x.encode('hex') for x in s)
def str2uint64(s):
    if len(s) == 0:
        print "str2uint64 has empty"
        return 0
    #print ':'.join(x.encode('hex') for x in s)
    return reduce(lambda x, y : x * 256 + y, [ord(c) for c in s])

def str2int16(s):
    if len(s) != 2:
        print "str2int16 len not match: ", len(s), " | ", str2hex(s)
        return 0
    v = str2uint64(s)
    n = 1 if v & 128 == 128 else 0
    v = v & 127
    if n == 1:
        v = -v
    return v

flvAudioSoundFormatMap = {
'0':"Linear PCM, platform endian",'1':"ADPCM",'2':'MP3','3':'Linear PCM, little endian',
'4':'Nellymoser 16 kHz mono','5':'Nellymoser 8 kHz mono','6':'Nellymoser',
'7':'G.711 A-lwa logarithmic PCM','8':'G.711 mu-law logarithmic PCM',
'9':'reserved','10':'AAC','11':'Speex','14':'MP3 8 kHz','15':'Device-specific sound'
}
flvAudioSoundRateMap = {
'0':'5.5 kHz','1':'11 kHz','2':'22 kHz','3':'44 kHz'       
}
flvAudioSoundSizeMap = {'0':'AAC sequence header','1':'AAC raw'}

def audioDataParse(datasize, audioData, isEncrypted):
    print "--- audio data ---"
    byte0uint64 = str2uint64(audioData[0])
    soundFormat  = byte0uint64 >> 4 
    soundRate    = byte0uint64 & 12 
    soundSize    = (byte0uint64 & 2) >> 1 
    aacPacktType = byte0uint64 & 1
    print "soundFormat  : ", soundFormat, " ", flvAudioSoundFormatMap.get(str(soundFormat)) 
    print "soundRate    : ", soundRate, " ", flvAudioSoundRateMap.get(str(soundRate)) 
    print "soundSize    : ", soundSize, " ", flvAudioSoundSizeMap.get(str(soundSize)) if soundFormat == 10 else ""
    print "aacPacktType : ", aacPacktType 
    print "payload      : ", "encrypted" if isEncrypted else "unencrypted"
    print "-----------------"


flvVideoFrameTypeMap = {
'1':'key frame(for AVC, a seekable frame)','2':'inter frame (for AVC, a non-seekable frame)',
'3':'disposable inter frame (H.263 only)','4':'generated key frame (reserved for server use only)',
'5':'video info/command frame'
}
flvVideoCodedIdMap = {
'2':'Sorenson H.263','3':'Screen video','4':'On2 VP6','5':'On2 VP6 with alpha channel',
'6':'Screen video version 2','7':'AVC'
}
flvVideoAVCPacketTypeMap = {
'0':'AVC sequence header','1':'AVC NALU',
'2':'AVC end of sequence (lower level NALU sequence ender is not required or supported)'      
}
def videoDataParse(datasize, videoData, isEncrypted):
    print "--- video data ---"
    byte0uint64 = str2uint64(videoData[0])
    frameType = byte0uint64 >> 4
    codedId   = byte0uint64 & 15

    # if codecId is avcif avc format, it the video tag header will additinal 4 bytes info, 
    # avcPacketType and compositonTime has real meaning 
    avcPacketType = str2uint64(videoData[1])
    compositonTime = str2uint64(videoData[2:5]) 

    print "frameType     : ", frameType, " ", flvVideoFrameTypeMap.get(str(frameType))
    print "codecId       : ", codedId, " ", flvVideoCodedIdMap.get(str(codedId))
    if codedId == 7: # avc format h.264 
        print "avcPacketType   : ", avcPacketType, flvVideoAVCPacketTypeMap.get(str(avcPacketType)) 
        print "compositonTime  : ", compositonTime
    print "payload      : ", "encrypted" if isEncrypted else "unencrypted"
    print "-----------------"

flvScriptDataTypeMap = {
'0':'Number','1':'Boolean','2':'String','3':'Object','4':'MovieClip (reserved, not supported)',
'5':'Null','6':'Undefined','7':'Reference','8':'ECMA array','9':'Object end marker',
'10':'Strict array','11':'Date','12':'Long string'
}

SCRIPT_DATA_TYPE_LEN = 16
scriptDataTypeFuncArray = [None for i in range(SCRIPT_DATA_TYPE_LEN)]

def genLevelPrefix(level):
    return '  ' * level + '--->'

''' Type 0 '''
def scriptDataNumber(datasize, scriptData, start, level): 
    prefix = genLevelPrefix(level)
    hexData = str2hex(scriptData[start:start+8])
    print prefix, hexData
    from struct import unpack 
    print prefix, "Number : ", unpack('d', scriptData[start+7:start-1:-1])  
    #print prefix, "Number : ", unpack('d', scriptData[start:start+8])  
    start += 8
    return start

''' Type 1 '''
def scriptDataBoolean(datasize, scriptData, start, level): 
    prefix = genLevelPrefix(level)
    print prefix, "Boolean : ", str2uint64(scriptData[start])
    start += 1
    return start

''' Type 2 '''
def scriptDataString(datasize, scriptData, start, level): 
    stringLength = str2uint64(scriptData[start:start+2])
    #print str2hex(scriptData[start:start+2])
    #print stringLength
    stringData = scriptData[start + 2:start + 2 + stringLength]
    prefix = genLevelPrefix(level)
    #print prefix, "String ", stringLength, ":"
    print prefix, stringData 
    start = start + 2 + stringLength 
    return start

''' Type 3 '''
def scriptDataObject(datasize, scriptData, start, level): 
    prefix = genLevelPrefix(level)
    print prefix, "Script Data Object"
    while True:
        objectEnd = scriptData[start:start+3]
        if 0 == ord(objectEnd[0]) and 0 == ord(objectEnd[1]) and 9 == ord(objectEnd[2]):
            print prefix, "--- Script Data Object ---"
            start += 3
            break  
        start = scriptDataObjectProperty(datasize, scriptData, start, level)
    return start

''' Type 8 '''
def scriptDataECMAArray(datasize, scriptData, start, level): 
    prefix = genLevelPrefix(level)
    arrayLen = str2uint64(scriptData[start:start+4])    
    print prefix, "ecma array Length  : ", arrayLen
    start += 4
    for i in range(arrayLen):
        start = scriptDataObjectProperty(datasize, scriptData, start, level + 1)

    objectEnd = scriptData[start:start+3]
    if not (0 == ord(objectEnd[0]) and 0 == ord(objectEnd[1]) and 9 == ord(objectEnd[2])):
        print "script data ecma array parse, object end not match: ", str2hex(objectEnd)
        sys.exit(1)
    start += 3
    return start

''' Type 10 '''
def scriptDataStrictArray(datasize, scriptData, start, level): 
    prefix = genLevelPrefix(level)
    arrayLen = str2uint64(scriptData[start:start+4])    
    print prefix, "strict array Length  : ", arrayLen
    start += 4
    for i in range(arrayLen):
        start = scriptDataValue(datasize, scriptData, start, level + 1)

    return start

''' Type 11 '''
def scriptDataDate(datasize, scriptData, start, level): 
    prefix = genLevelPrefix(level)    
    print prefix, "DateTime : ", str2hex(scriptData[start:start+4])
    print prefix, "Date Local date time offset: ", str2int64(scriptData[start + 4, start + 6])
    start += 6
    return start

''' Type 12 '''
def scriptDataLongString(datasize, scriptData, start, level): 
    stringLength = str2uint64(scriptData[start:start + 4])
    stringData = scriptData[start + 4:start + 4 + stringLength]
    prefix = genLevelPrefix(level)
    print prefix, "Long String ", stringLength, " :"
    print prefix, stringData 
    start = start + 4 + stringLength 
    return start

def scriptDataObjectProperty(datasize, scriptData, start, level):
    prefix = genLevelPrefix(level)
    print prefix, "--- Object Property --- "
    print prefix, "Property Name: "
    start = scriptDataString(datasize, scriptData, start, level + 1)
    print prefix, "Property Value KAKA: "
    start = scriptDataValue(datasize, scriptData, start, level + 1) 
    #print prefix, "--- --- --- --- --- --- "
    print prefix
    return start 

# init script data call func
scriptDataTypeFuncArray[0] = scriptDataNumber
scriptDataTypeFuncArray[1] = scriptDataBoolean
scriptDataTypeFuncArray[2] = scriptDataString
scriptDataTypeFuncArray[3] = scriptDataObject
scriptDataTypeFuncArray[8] = scriptDataECMAArray 
scriptDataTypeFuncArray[10] = scriptDataStrictArray 
scriptDataTypeFuncArray[11] = scriptDataDate
scriptDataTypeFuncArray[12] = scriptDataLongString

def scriptDataValue(datasize, scriptData, start, level):
    prefix = genLevelPrefix(level)
    valueType = str2uint64(scriptData[start])
    if valueType >= SCRIPT_DATA_TYPE_LEN:
        print prefix, "script data value parse, value type out of range: ", valueType
        sys.exit(1)
    callfunc = scriptDataTypeFuncArray[valueType]
    if callfunc:
        #print prefix, "Script Data Value :", valueType, " ", flvScriptDataTypeMap.get(str(valueType))
        start = callfunc(datasize, scriptData, start + 1, level)
    else:
        print prefix, "script data value parse, could find func for type: ", valueType, " ", flvScriptDataTypeMap.get(str(valueType))
        sys.exit(1)
    
    return start

def scriptDataParse(datasize, scriptData, start, level):
    # ScriptTagBody 
    # 1. Name it should be SCRIPTDATASTRING 
    nameType = str2uint64(scriptData[0])
    nameValueLength = str2uint64(scriptData[1:3]) # 2 bytes 
    nameValueData = str2hex(scriptData[3: 3 + nameValueLength])
    print "Name Type    : ", nameType, flvScriptDataTypeMap.get(str(nameType))
    print "Name Length  : ", nameValueLength
    print "Name Data    : ", nameValueData, scriptData[3:3+nameValueLength]

    # 2. Value it should be SCRIPTDATAECMAARRAY
    valuePos = 3 + nameValueLength
    valueType = str2uint64(scriptData[valuePos]) 
    print "Value Type          : ", valueType, flvScriptDataTypeMap.get(str(valueType))  
    scriptDataECMAArray(datasize, scriptData, valuePos + 1, level + 1 )


count = 0
header = []

file_info = {}
header = f.read(9)
first_previous_tage_size = f.read(4)

header_info = {}
file_info['header'] = header_info
header_info['signature'] = header[0:3]
header_info['version'] = ord(header[3])
header_info['typeflags_audio'] = (str2uint64(header[4]) & 7) >> 2
header_info['typeflags_video'] = (str2uint64(header[4]) & 1)

data_offset = str2uint64(header[5:])
#header_info['data_offset'] = {str2hex(header[5:]):data_offset}
header_info['data_offset'] = data_offset

file_info['first_previous_tage_size'] = str2hex(first_previous_tage_size) 

print 'flv file info:'
print '--------- header info ---------'
print 'header:      ', header_info['signature']
print 'version:     ', header_info['version']
print 'typeflags_audio:   ', header_info['typeflags_audio']
print 'typeflags_video:   ', header_info['typeflags_video']
print 'data_offset: ', header_info['data_offset']
print '-------------------------------'

sys.exit(1)

count = 13
flvtag_index = 1
while count < file_size:
    flvtag_first11 = f.read(11) # get flvtag first 11bytes
    if flvtag_first11 == '':
       break
    if len(flvtag_first11) < 11:
        print "flvtag read error at flvtag[", flvtag_index, "]"
        break
    byte0hex = str2hex(flvtag_first11[0])
    byte0uint64 = str2uint64(flvtag_first11[0]) 
    isEncrypted = (byte0uint64 & 32) >> 5 
    tagType = byte0uint64 & 31 
    datasize = str2uint64(flvtag_first11[1:4])
    timestamp = str2uint64(flvtag_first11[4:7])
    timestampExtended = str2uint64(flvtag_first11[7])
    realtimestamp = (timestampExtended << 24) + timestamp
    streamID  = str2hex(flvtag_first11[8:]) 
 

    print "byte0               : ", byte0hex 
    print "tagType from byte0  : ", tagType 
    print "datasize            : ", datasize 
    print "timestamp           : ", timestamp 
    print "timestampExtended   : ", timestampExtended 
    print "realtimestamp       : ", realtimestamp 
    print "streamID            : ", streamID

    data = f.read(datasize) 
    if datasize > 0:
        if tagType == 8:
            audioDataParse(datasize, data, isEncrypted)
        if tagType == 9:
            videoDataParse(datasize, data, isEncrypted)
        if tagType == 18 and not isEncrypted:
            print "--- script data ---"
            scriptDataParse(datasize, data, 0, 0)
            print "-----------------"

    previousTagSizeStr = f.read(4)
    previousTagSize = str2uint64(previousTagSizeStr)
    print "previousTagSize     : ", previousTagSize
    print '-------------------------------'


    count += datasize + 11 + 4 
    #count += previousTagSize 
    flvtag_index += 1
    #if flvtag_index > 2:
        #break 

print flvtag_index 
print count
f.close()

