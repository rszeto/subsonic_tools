"""
Subsonic Tools | Command line tools for Subsonic Music Streamer

Modified by Ryan Szeto (szetor@umich.edu). (c) 2018
Original author: Jan Jonas (mail@janjonas.net)
License: GPLv2 (http://www.gnu.org/licenses/gpl-2.0.html)
"""

import json
import pdb
import sys
import os
import re
import requests
import xml.etree.ElementTree as ET
import urllib
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from pprint import pprint

from mutagen.easyid3 import EasyID3

subsonic_namespace = "http://subsonic.org/restapi"
subsonic_client = "Subsonic-Tools"
subsonic_apiVersion = "1.8.0"

def create_subsonic_call_fn(subsonic_url, subsonic_user, subsonic_password, verbose):

    def subsonic_call(command, params = []):
        # Construct the REST call
        url = "%s/rest/%s.view?v=%s&c=%s&%s" % (subsonic_url, command, subsonic_apiVersion,
                                                subsonic_client, urllib.urlencode(params, True))
        if verbose:
            print('Accessing URL: %s' % url)

        # Send the request
        response = requests.get(url, verify=True, auth=(subsonic_user, subsonic_password))
        if verbose:
            print('Received response:')
            print(response.text.encode('utf-8'))

        if response.status_code != 200:
            raise Exception("Subsonic REST API returned status code %s" % response.status_code)

        # Parse the response (obtain the content and any errors)
        root = ET.fromstring(response.text.encode('utf-8'))
        error = root.find("{%(ns)s}error" % {"ns": subsonic_namespace})
        
        if error is not None:
            raise Exception("Error (Code: %(code)s, Text: %(text)s)" % {
                "code": error.get("code"),
                "text": error.get("message")
            })
        else:
            # First child is response object (unless an empty <subsonic-response> object is
            # returned)
            return root[0] if len(root) > 0 else None

    return subsonic_call

def sort_playlists(args):
    # Prepare with data from config file
    with open(args.config_path, 'r') as f:
        config = json.load(f)
    music_root = config['music_root']
    subsonic_call = create_subsonic_call_fn(config['server_url'], config['user'],
                                            config['password'], args.verbose)
     
    # Get list of playlists
    playlists = subsonic_call("getPlaylists")
    for playlist in playlists.iter("{%(ns)s}playlist" % {"ns": subsonic_namespace}):
    
        # Get the songs in the current playlist
        playlist_id = playlist.get("id")
        playlist = subsonic_call("getPlaylist", {"id": playlist.get("id")})

        song_titles = []
        song_ids = []
        for entry in playlist.iter("{%(ns)s}entry" % {"ns": subsonic_namespace }):
            # Get the path to the current music file
            file_path = os.path.join(music_root.encode("utf-8"), entry.get("path").encode("utf-8"))
            
            # Store the ID3 title of the current song
            with open(file_path, 'rb') as f:
                id3_tag = EasyID3(f)
                song_title = id3_tag['title'][0].encode('utf-8')
            song_titles.append(song_title)

            # Store the Subsonic song ID
            song_id = entry.get('id')
            song_ids.append(song_id)
        
        # Sort the song IDs by title
        sorted_indexes = argsort(song_titles, key=lambda i: song_titles[i].lower())
        sorted_song_ids = index_select(song_ids, sorted_indexes)

        # Remove all songs
        subsonic_call('updatePlaylist', {
            'playlistId': playlist_id,
            'songIndexToRemove': range(len(song_ids))
        })

        # Add all songs in sorted order
        subsonic_call('updatePlaylist', {
            'playlistId': playlist_id,
            'songIdToAdd': sorted_song_ids
        })

    print "Done."    

def argsort(seq, key=None):
    """Adapted from https://stackoverflow.com/a/6979121"""
    if key is None:
        key = seq.__getitem__
    return sorted(range(len(seq)), key=key)

def index_select(seq, indexes):
    ret = []
    for i in indexes:
        ret.append(seq[i])
    return ret

def main():
    print('Licensed under the GPLv2 (http://www.gnu.org/licenses/gpl-2.0.html). Distributed on an'
        ' "AS IS" basis without warranties or conditions of any kind, either express or implied.\n')

    parser_parent = ArgumentParser()
    parser_parent.add_argument('--verbose', action='store_true',
                               help='Flag to print extra information')
    subparsers = parser_parent.add_subparsers()
    parser_sort_playlists = subparsers.add_parser('sort_playlists')
    parser_sort_playlists.add_argument('--config_path', type=str, default='config.json',
                                       help='Path to the configuration file')
    parser_sort_playlists.set_defaults(func=sort_playlists)

    args = parser_parent.parse_args()
    args.func(args);

if __name__ == "__main__":
    main()
