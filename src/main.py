from getPlaylist import getPlaylist
import webbrowser
import time
import audacityClient
from assignTrackID3Tags import applyTrackInfo

from tqdm import tqdm

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

import io
import requests

load_dotenv()

trackDurationInMsCol = "Durée du titre (ms)"
trackUrlCol = "URI du titre"
trackNameCol = "Nom du titre"
trackArtistCol = "Nom(s) de l'artiste"
trackImageURL = "URL de l'image de l'album"
safetyMarginInSeconds = 1

dataFolder = "/Users/theobernier/Music/Downloads/dowload-26-10-25"
playlistFolder = "/Users/theobernier/Music/Downloads/dowload-26-10-25"
playlistFileName = "track_infos.csv"





def authenticateToSpotify():
    scope = "user-modify-playback-state"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    return sp

def playSpotifyTrack(track):
    print('Playing ' + track[trackArtistCol] + ' - ' + track[trackNameCol] +' ... ')
    webbrowser.open(track[trackUrlCol])
    return

def startRecording(client):
    print('Recording ... ')
    client.write("Record2ndChoice")
    return

def stopRecording(client):
    print('Stopping recording')
    #client.write("Pause")
    client.write("DefaultPlayStop")
    print('Recording stopped')
    return

def recordTrack(client, track):
    selectTrackLength(client, track)
    startRecording(client)

def selectTrackLength(client, track):
    trackStart = 0
    trackEndInSeconds = round(track[trackDurationInMsCol] / 1000) + safetyMarginInSeconds
    client.write(f'SelectTime: End="{trackEndInSeconds}" RelativeTo="ProjectStart" Start="0"')

def waitForClient(client, statusSubstring):
    audacityStatus = getClientStatus(client)
    while statusSubstring not in audacityStatus.strip():
        print("status", audacityStatus)
        print("waiting for audacity operation to finish")
        time.sleep(1)
        audacityStatus = getClientStatus(client)
    print("client finished with status", audacityStatus)

def waitForClientNormalize(client):
    waitForClient(client, "BatchCommand finished: OK")

def waitForClientExport(client):
    waitForClient(client, "Exported to MP3")

def exportToMp3(client, track):
    client.write("SelectAll")
    time.sleep(0.5)
    getClientStatus(client)
    client.write(f"Normalize: ApplyVolume=1 RemoveDcOffset=1 PeakLevel=-1 StereoIndependent=0")
    time.sleep(0.5)
    waitForClientNormalize(client)


    client.write(f"Export2: Filename={buildTrackFilePath(track)} NumChannels=2")
    waitForClientExport(client)
    client.write("SelectAll")
    client.write("RemoveTracks")
    time.sleep(0.5)

def getClientStatus(client):
    return client.read()

def buildTrackFilePath(track):

    fileName = "%s--%s" % \
               (
                   track[trackNameCol].replace(" ", "_").replace("\\", "-").replace("/", "_").replace('"', "in"),
                   track[trackArtistCol].replace(" ", "_").replace("\\", "-").replace("/", "_").replace('"', "in")
               )
    return f"{dataFolder}/{fileName}.mp3"

def assignTrackInfos(track):
    print("Assigning track infos")
    albumCover = getTrackAlbumCover(track)
    applyTrackInfo(buildTrackFilePath(track), track, albumCover=albumCover)



def getTrackAlbumCover(track):
    coverUrl = track[trackImageURL]
    data = requests.get(coverUrl).content
    return io.BytesIO(data)

def pauseSpotifyPlayback(spotifyClient):
    pauseRetryCounter = 0
    pauseRetryLimit = 5
    try:
        spotifyClient.pause_playback()

    except:
        if pauseRetryCounter < pauseRetryLimit:
            print("WARNING: Failed to pause spotify playback, reauthenticating to spotify and retrying now")
            time.sleep(1)
            spotifyClient = authenticateToSpotify()
            spotifyClient.pause_playback()
        else:
            print("maximum retries exhausted, exiting program")
            raise ConnectionResetError(54, 'Connection reset by peer')


def main():
    spotifyClient = authenticateToSpotify()
    tracks = getPlaylist(f"{playlistFolder}/{playlistFileName}")
    client = audacityClient.PipeClient()

    for index, track in tqdm(tracks.iterrows(), desc="Loading...", total=tracks.shape[0]):
        remaining_time_in_ms = tracks[trackDurationInMsCol][index:].sum()
        print("remaining time: ", remaining_time_in_ms/(60*1000), " min")

        if index != 5:
            continue
        # if index == 5:
        #     exportToMp3(client, track)
        #     assignTrackInfos(track)
        #     continue

        recordTrack(client, track)

        playSpotifyTrack(track)
        time.sleep(track[trackDurationInMsCol] / 1000 + safetyMarginInSeconds)
        pauseSpotifyPlayback(spotifyClient)

        exportToMp3(client, track)
        assignTrackInfos(track)

if (__name__=="__main__"):
    main()
