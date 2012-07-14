#! /usr/bin/python
# -*- coding: euc-jp -*-;

import getopt, sys, os, re
import datetime 
from time import strptime

def usage():
    print "Usage:"
    print sys.argv[0],"channel [start_date] start_time [end_date] end_time [-t title]"
    print sys.argv[0],"channel [start_date] start_time duration [-t title]"
    print "  channel is fm, r1, r2"
    print "  start_date and end_date should be YY/MM/DD or MM/DD format"
    print "      if start_date not specied, use today as start_date"
    print "      if end_date not specified, end_date sets on the same-day to start_date."
    print "  start_time and end_time should be HH:MM format"
    print "     late night time, such as 26:00 is also possible."
    print "  duration should be 90m or 1h30m format"

def get_opts():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "t:", ["title="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    result = [opts, args]
    return result

def norm_date(dt_str):
    """���դ�ʸ����MM/DD�ξ�硤YY/MM/DD�ˤ����֤�"""
    res = re.match('[0-9]+/[0-9]+/[0-9]+', dt_str)
    if res == None: # MM/DD format
        year = datetime.datetime.today().strftime("%Y")
        (month, day) = dt_str.split('/')
    else:  # YY/MM/DD format
        (year, month, day) = dt_str.split("/")

    date_str = year + "-" + month + "-" + day
    # print "dt_str:", dt_str
    return date_str

def norm_time(date_str, time_str):
    """���դȻ����ʸ�����ɸ�ಽ���롥
    �⤷���郎24:00�ʹߤξ�硤�����-24���Ƥ���date���֥������Ȥ��ä�
    ���timedelta��1���ä���(date���֥������Ȥ�hour<24��ɬ�פΤ���)
    ��������26:00���餤�ޤǤ����Ȥ�ʤ�����ʤΤǡ�48:00 �ʾ�λ�����Բ�"""
    (str_year, str_month, str_day) = date_str.split("-")
    year = int(str_year)
    month = int(str_month)
    day = int(str_day)

    (str_hour, str_minute) = time_str.split(":")
    hour = int(str_hour)
    minute = int(str_minute)
    day_over = 0
    if hour >= 24:
        hour = hour - 24
        day_over = 1

    date_obj = datetime.datetime(year, month, day, hour, minute)
    if day_over == 1:
        date_obj = date_obj + datetime.timedelta(days=1)

    return date_obj

def norm_duration(d):
    """Ͽ����֤λ����ʬñ�̤˴�������"""
    t = d.lower()
    if t.find('h') > 0:  # ex: 1h30m
        (h, m) = t.split('h')
        # print "h:",h, "m:",m
        mm = m.rstrip('m')
        if mm != '':
            duration = int(h)*60 + int(mm)
        else:
            duration = int(h)*60
    else:
        mm = t.rstrip('m')
        duration = int(mm)
    return duration

def get_parms():
    """������ꥹ�Ȥȸ��ƽ��֤˥ѡ������롥
    �����ȥ����ꤹ��� -t �ȶ���opts���֤äƤ��롥
    �����ν��֤�"�����ͥ�" "���ϻ���" {"��λ����" | "Ͽ������" } �ν硥 
    ���ϻ����λ����Ȥ�����դλ��̵꤬����Сֺ����ס�
    �������ϡ�����Ū�� 25:00 �ߤ����ʻ�����ǽ��
    Ͽ�����֤� 90m �� 1h30m �η���h �� m ��̵���ȥ��顼�ˤʤ�"""
    opts, argvs = get_opts()
    #argvs = sys.argv
    print("opts:{0} argvs:{1}".format(opts,argvs))
    argc = len(argvs)
    if argc < 3 or argc > 5:
        print(argvs, len(argvs))
        usage()
        sys.exit(1)

    o, title = opts.pop(0)
    channel = argvs.pop(0)
    start_flag = 0
    duration = 0
    while len(argvs) > 0:
        if (start_flag == 0):
            i = argvs.pop(0)
            if re.match('[0-9]+/[0-9]+', i): # date part
                begin_date_str = norm_date(i)
                i = argvs.pop(0)
                begin_time_str = i
            else:
                begin_date_str = datetime.datetime.today().strftime("%Y-%m-%d")
                begin_time_str = i
            start_flag = 1
            begin = norm_time(begin_date_str, begin_time_str)

        else:
            i = argvs.pop(0)
            if re.match('[0-9]+/[0-9]+', i): # date part
                end_date_str = conv_date_format(i)
                i = argvs.pop(0)
                end_time_str = i
            elif re.search('[HhMm]', i) != None:
                duration = norm_duration(i)
                end_date_str = 'none'
                end_time_str = 'none'
            else:                    
                end_date_str = begin_date_str
                end_time_str = i

            if duration == 0:
                end = norm_time(end_date_str, end_time_str)

    if duration == 0:
        interval = end - begin
        duration = interval.days*24*60 + interval.seconds/60

    return(channel, begin, duration, title)

def make_script(channel, duration, title):
    """Ͽ���ѤΥ����륹����ץȤ��롥
    �����륹����ץȤ��֤���� ~/radiru_scripts/ �ǡ�Ͽ���ǡ������֤����
    ~/MP3/ ������(�ѹ���)������python������ץȤ�PID��Ͽ���ѥ����륹����ץȤ�
    �ե�����̾��ή�Ѥ��졤���Υե������at���ޥ�ɤǻ��ꤷ������˼¹Ԥ��롥"""
    scriptdir = os.path.expanduser("~/radiru_scripts")
    musicdir = os.path.expanduser("~/MP3")
    my_pid = os.getpid()
    # print("scriptdir:{0},musicdir:{1}".format(scriptdir,musicdir))
    if channel == 'r1':
        playlist='http://mfile.akamai.com/129931/live/reflector:46032.asx'
    elif channel == 'r2':
        playlist='http://mfile.akamai.com/129932/live/reflector:46056.asx'
    elif channel == 'fm':
        playlist='http://mfile.akamai.com/129933/live/reflector:46051.asx'
    else:
        print("channel set error:{0}".format(channel))
        usage()
        sys.exit(1)

    if os.access(scriptdir, os.R_OK) == False:
        print("{0} not writable.".format(scriptdir))
        sys.exit(1)
    
    scriptname = scriptdir + "/" + str(my_pid)
    f = open(scriptname, "w")

    lines = []
    lines.append("#!/bin/sh")
    lines.append("sleep 10")  
    lines.append("mkfifo /tmp/fifo_{0}".format(str(my_pid)))
    lines.append("file={0}/{1}-`date +\"%F-%H-%M\"`.mp3".format(musicdir, title)) 
    lines.append("(mplayer -slave -input file=/tmp/fifo_{0} -playlist {1} -ao pcm:file=/dev/stdout -vc null -really-quiet -quiet | lame -r --quiet -q 4 - $file 2> /dev/null) &".format(my_pid, playlist))
    lines.append("sleep {0}m".format(duration))
    lines.append("echo 'quit' > /tmp/fifo_{0}".format(my_pid))
    lines.append("rm -f /tmp/fifo_{0} {1}\n".format(my_pid, scriptname))
    script = "\n".join(lines)

    f.write(script)
    f.close
    return(scriptname)

def register_script(script, begin):
    begin_str = begin.strftime("%H:%M %m/%d/%Y")
    cmd = "at {0} -f {1}".format(begin_str, script)
    print cmd
    result = os.system(cmd)
    return result
    
def main():
    (channel, begin, duration, title) = get_parms()
    print("channel:{0}".format(channel))
    print("begin time:{0}".format(begin.strftime("%m/%d/%Y %H:%M")))
    print("duration(m):{0}".format(duration))
    if len(title) > 0:
        print("title:{0}".format(title))
    else:
        title=channel

    now = datetime.datetime.today()
    if begin < now:
        print("Time set error! Begin time already gone.")
        sys.exit(1)

    if duration < 0:
        print("Time set error! Recording period becomes minus.")
        sys.exit(1)
    elif duration < 5:
        print("Warning. Recording period under 5minutes.")
    elif duration > 180:
        print("Warning. Recording period over 3hrs.")

    scriptname = make_script(channel, duration, title)
    result = register_script(scriptname, begin)

    if result != 0:
        print("register_script error. cannot registered recording script.")
        sys.exit(1)

if __name__ == "__main__":
    main()
