
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC

def applyTrackInfo(filePath, trackInfo, *args, **kwargs):
    mp3file = MP3(filePath, ID3=EasyID3)
    albumCover = kwargs.get('albumCover', None)
    mp3file['title'] = trackInfo['Nom du titre']
    mp3file['album'] = trackInfo["Nom de l'album"]
    mp3file['artist'] = trackInfo["Nom(s) de l'artiste"]
    mp3file.save()

    if (albumCover):
        mp3file = ID3(filePath)
        mp3file['APIC'] = APIC(
                encoding=3, # 3 is for utf-8
                mime='image/png', # image/jpeg or image/png
                type=3, # 3 is for the cover image
                desc=u'Cover',
                data=albumCover.read()
            )
        mp3file.save()