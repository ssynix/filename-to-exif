# filename-to-exif
Updating EXIF date taken of photos from their filename.

When updating/rerooting my phone, I use DriveSync to backup pictures that I don't necessarily want to store on my Google Photos, or pictures that I still want to have locally saved on my phone organized by folders.

The problem is that the creation date is lost during the upload process (same thing happens regardless of backup method, adb, MTP, etc...), and some of these files don't have any additional metadata (e.g. screenshots, snapchats).

The good thing is that in most cases, the date is saved as part of the filename. I try to extract that date using a couple of common patterns that I found in my own data and add it to the files metadata.

If the corresponding Google Drive backup is synced on the computer, then this script can directly modify its contents and sync the metadata back to the device where Google Photos can pick it up and not screw up the order.
