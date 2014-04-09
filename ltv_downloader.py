#!/usr/bin/env python
#coding: utf-8

__author__ = 'Flavio'

from sys import argv

import os
import urllib2
import re
import logging
import rarfile


def main(torrent_id, torrent_name, torrent_path):
    '''
    '''

    id_list = __get_subtitle_ids(torrent_name)

    logging.info('Found %d subtitle(s) that match the search' % len(id_list))

    if not id_list:
        trimmed_name = re.findall('^(.*?S\d+E\d+)', torrent_name)[0]
        id_list = __get_subtitle_ids(trimmed_name)

        logging.info('Found %d subtitle(s) that match the search' % len(id_list))

        if not id_list:
            logging.info('Quitting')
            exit(2)

    subtitle_file = __download_subtitle(id_list[0])

    __extract_file(subtitle_file.name, torrent_name, torrent_path)
    # __extract_file('5342c7f4f1392.rar', torrent_name, torrent_path)

    logging.info('Deleting subtitle rar file')

    os.remove(subtitle_file.name)


def __extract_file(file_name, torrent_name, torrent_path):
    '''
    Extracts the downloaded RAR file to the given path
    '''

    logging.info('Extracting subtitle %s', file_name)

    try:
        rarfile.UNRAR_TOOL = '/usr/local/bin/unrar'
        rar = rarfile.RarFile(file_name)

        logging.debug(rar.namelist())

        preferred_subtitle_name = torrent_name + '.srt'
        if preferred_subtitle_name in rar.namelist():
            rar.extract(preferred_subtitle_name, torrent_path)

            logging.info('Extracted preferred subtitle %s', preferred_subtitle_name)
        else:
            distributor_name = re.findall('.*\-(.*?)$', torrent_name)[0]
            quality = re.findall('\.(\d+)p\.', torrent_name)[0]
            proper = re.findall('(PROPER)?', torrent_name)[0]

            logging.info('Trying to find subtitle for distributor %s with quality %s', distributor_name, quality)

            for sub_name in rar.namelist():
                lower_sub_name = sub_name.lower()
                if distributor_name.lower() in lower_sub_name and \
                                quality.lower() in lower_sub_name and \
                        (proper and proper.lower() in lower_sub_name):
                    rar.extract(sub_name, torrent_path)

                    logging.info('Extracted subtitle %s', sub_name)
                    return

    except Exception, e:
        logging.error('An unexpected error ocurred while extracting the subtitle (%s)' % e)


def __download_subtitle(subtitle_id):
    '''
    Downloads the subtitle with the given id
    '''

    logging.info('Downloading subtitle %s' % subtitle_id)

    try:
        http_result = urllib2.urlopen('http://legendas.tv/downloadarquivo/' + subtitle_id)

        with open(os.path.basename(subtitle_id+'.rar'), "wb") as local_file:
            local_file.write(http_result.read())

        logging.info('Downloaded subtitle %s' % local_file.name)

        return local_file
    except urllib2.HTTPError, e:
        logging.error('Failed to download subtitle %s (%s)' % (subtitle_id, e))


def __get_subtitle_ids(torrent_name):
    '''
    Retrieves a list of ids matching the given torrent name
    '''

    logging.info('Fetching subtitle ids: %s' % (torrent_name))

    search_url = 'http://legendas.tv/util/carrega_legendas_busca/termo:%(tname)s/id_idioma:1' % {'tname': torrent_name}

    try:
        opener = urllib2.build_opener()
        opener.addheaders = [('X-Requested-With', 'XMLHttpRequest')]
        http_result = opener.open(search_url)

        http_text = http_result.read()

        return re.findall('/download/(.*?)/', http_text)
    except urllib2.HTTPError, e:
        logging.error('Failed to fetch subtitle download (%s)' % e)
        exit(1)

    return []

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG if len(argv) == 1 else logging.INFO)

    main(argv[1:])