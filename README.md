# filename-to-exif
Updating EXIF date taken of photos from their filename. Get `brew install exiftool`.

Run `main.py --help` to start.

When updating/rerooting my phone, I use DriveSync to backup pictures that I don't necessarily want to store on my Google Photos, or pictures that I still want to have locally saved on my phone organized by folders.

The problem is that the creation date is lost during the upload process (same thing happens regardless of backup method, adb, MTP, etc...), and some of these files don't have any additional metadata (e.g. screenshots, snapchats).

The good thing is that in most cases, the date is saved as part of the filename. I try to extract that date using a couple of common patterns that I found in my own data and add it to the file's metadata.

If the corresponding Google Drive backup is synced on the computer, then this script can directly modify its contents and sync the metadata back to the device where Google Photos can pick it up and not screw up the order.

## Actual results
###1. Duplicates:
If photos are already synced to Google Photos, then modifying their EXIF data is not going to simply work. What I realized is that Google's duplicate detection is extremely simplistic (probably relying on file hash or something similar), and modifying any EXIF data will only result in duplicates. One simply with the original filename (cloud), the other including the whole image path on the device. Very disappointing for an app that lets you search your image library for 'Dogs'.

**Solution**: you have to delete the older backed up files from Google Photos, and reupload them with new EXIF data. 

###2. Local out-of-order, but not on the cloud:
Another situation that I ran into was that the desktop website would be unaffected by my change, but locally I'd see an out-of-order version of the same picture in my library, even though the image details would show the correct date. I realized that this has to do with the local filesystem dates of the images. 

**Solution**: the only solution I found was to generate a script alongside my EXIF changes that would `touch -amd` the correct date on the phone's filesystem itself. Since my phone's rooted, I executed the script on the device and rebooted it. Afterwards, my gallery app (Quickpic) was able to sort the photos properly.

I had to fully wipe Google Photos app data and let it resync with the local filesystem for it to behave...

# Alternative to this repo
Just fucking get over your OCD and upload everything to Google Photos, keep none of it locally on the device, and organize things into albums if you really care about folder structure.

The worse thing about this is that there's no way to automatically add pictures to albums (e.g. automatically save pics in folder *Snapchat* to the album *Snapchat*), and there's no way to have nested albums.
