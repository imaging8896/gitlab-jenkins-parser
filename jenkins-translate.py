import urllib2
import os
import sys
import time
import socket
import argparse


"""
Simple script for Gitlab-CI runner, translating Jenkins console output
"""

__author__ = 'Vladimir Eremeev'


def get_build_console_for_sha1(url, sha1):
    return '{}/scm/bySHA1/{}/consoleText'.format(url, sha1)


def parse_console(build_con):
    retcode = 0

    if build_con:
        total_read_lines = 0
        finished_line = None
        read_attempts = 0
        retry_times = 0

        while not finished_line:
            current_read_lines = 0
            try:
                for line in urllib2.urlopen(build_con).readlines():
                    current_read_lines += 1
                    if current_read_lines >= total_read_lines:
                        print line,
                        total_read_lines += 1
                        sys.stdout.flush()
                        if line.startswith('Finished: '):
                            finished_line = line
            except urllib2.HTTPError as e:
                print "Job hasn't finished..., retry"
                print e.code
                if e.code == 404:
                    time.sleep(2)
                    read_attempts += 1
                    if read_attempts > 5:
                        retcode = 1
                        break
            except socket.timeout:
                time.sleep(2)
                retry_times += 1
            except urllib2.URLError as e:
                print "Un-expected exception" + str(e)
                time.sleep(2)
                retry_times += 1
                if retry_times == 90:
                    raise Exception("Unstable network, unable to connect to jenkins...")
        
        if finished_line and ('FAILURE' in finished_line or 'UNSTABLE' in finished_line):
            retcode = 1

    print "retcode = ", retcode
    if retcode:
        print "="*50
        print "WARNING! " * 3
        print "   This is only a TRANSLATION of the real build output!"
        print "   Pressing 'Retry build' button will just reload the same page!"
        print "="*50
        print "Go to Jenkins and run rebuild, if you wanna rebuild"
        print "="*50

    return retcode


def main():
    parser = argparse.ArgumentParser(description='jenkins translation')
    parser.add_argument('-u', type=str, required=True,
                        help='Jenkins job URL')

    args = parser.parse_args()

    url = args.u
    sha1 = os.getenv('CI_BUILD_REF')

    print "Looking for job, building {}".format(sha1)
    sys.stdout.flush()

    for i in range(3):
        bc = get_build_console_for_sha1(url, sha1)
        if bc:
            break

    print "Found: {}".format(bc)
    sys.stdout.flush()

    return parse_console(bc)


if __name__ == '__main__' :
    sys.exit(main())