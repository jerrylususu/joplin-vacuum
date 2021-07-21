# joplin-vacuum
Removes attachments (resources) that are not referred (orphaned) in Joplin. 

**:warning: Always backup and use at your own risk! :warning:**

Tested with Joplin 2.1.9 (prod, win32) Revision: 882d66383 + Python 3.8. 

## Requirements

Python 3.6+ (for `f-string`)

No third-party dependencies.

## How it works?
When exporting notes to a JEX file, the attachments not referred will be ignored. JEX file is just a TAR file, and by reading the attachment ids under its `resources` folder, a list of referred attachment can be created. 

In Joplin, a full list of all attachments can be found via `Tools` - `Note Attachments...`. Joplin Data API also allows the list to be fetched programmatically. 

Thus, the attachments that are not referred (orphaned) can be calculated using the difference between the all attachment set and the referred attachment set.

### Related Links
- The issue of orphaned resources: [orphaned resources don’t get deleted - Issue #932 - Joplin](https://github.com/laurent22/joplin/issues/932)
- A cleaning solution based on direct DB access: [patrick-atgithub/joplintool](https://github.com/patrick-atgithub/joplintool)
## Usage
```
usage: vacummer.py [-h] [--port PORT] [--token TOKEN] [--limit LIMIT] [--confirm] [--test-del-1] jex_path

positional arguments:
  jex_path       Path to the JEX file

optional arguments:
  -h, --help     show this help message and exit
  --port PORT    the port used to connect to Joplin, leave blank for auto query
  --token TOKEN  override API token
  --limit LIMIT  pagenation limit for querying attachments from Joplin
  --confirm      Confirm deletion
  --test-del-1   (For testing purpose) Removing one not referred attachment. Need to be used with confirm.
```

## Recommend Procedure

1. Backup the Joplin database, by close Joplin and copy the `joplin-desktop` folder. (The full path can be find using the `Settings - General` panel)

2. Disable automatic synchronization for now, in order to prevent sync being triggered during the vacuum process. (`Settings - Synchronization - Synchronization interval - Disabled`) Also, do not perform any update on other clients to avoid versioning issues.

3. Start Joplin, and export all notes to a JEX file. (`File - Export All - JEX`)

4. Run the script in dry-run mode. For the first run you will need to grant access from Joplin GUI. Check if the orphaned files found are actually orphan or not. 
   ```bash
   python vacuum.py [JEX_PATH]
   ```

5. Run the script using `--test-del-1` and `--confirm` flag. This will removes 1 orphaned attachment while leaving others intact. This step checks if everything is working, including the deletion operation. Try to initiate sync after this step. If Joplin shows `Removing remote object: 1` and finishes the sync, then it's good to go.
    ```bash
    python vacuum.py [JEX_PATH] --confirm --test-del-1
    ```

6. If it works fine, only use `--confirm` flag to remove all orphaned attachments.
    ```bash
    python vacuum.py [JEX_PATH] --confirm
    ```

7. Perform a manual sync (by pressing `Ctrl+S` or click the `Synchronize` button), and check the count of `Removing remote object` is as expected. If the manual sync finished successfully, then you can enable the automatic sync, as well as manually sync on other devices.

## Additional Info

1. It is possible to perform the vacuum process without human intervention (e.g. use `cron` to schedule). But it is not recommended. First, you will need other tools that can create a JEX export programmatically. Then, performing the vacuum without disabling all writing may cause inconsistencies on states. 

## Example Output

```
$ python vacuum.py .\2021-07-21.jex --confirm
trying port 41184 200 OK port find!
loading token from file
requesting page 1... 200 OK got 26, total 26, has_more False
referred: 17, all 26
orphaned count: 9

id - filename
--------------------------------------
60414bdd2c3a493a8c9a06be82130858 - C7intaNotes_8aaaae945ac54d0588df35428e123db5.png
2f67c439207a4cb6bcb29068bf21d8fa - cintaanltesa-14100-3_c971215474ae42c2b30446b7f0217220.jpg
defd6c6ff6914ca98b960d2170b721ab - 3691d864f3730b2dcbc59c116338cc27.png
989b920202a241cbb4dde6c381d6884a - df83c2a0c7da98c08b00cfd6ea08d636.png
2556556e5a0c4b969b0b188154aa4b6d - 6ad4a4e235c9f6384b9da11c323f0fcd.png
31206111f5a54d97ba312f2257b62c46 - 640_wx_fmt_gif_tp_webp_wxfrom_5__f9b95901a1e04478a1b6b84682acfd26.gif
1765a4bc9db54414968c2d6265683b54 - cintaanltesa-14100-5_92fcfd8df37b48cc9cc251ed3a05e277.jpg
0a9b69625f1d4592ad3727f95676074f - cintaanltesa-14100-4_8a657a4c6a644daca790f6ccf5505094.jpg
5c7ec35321dc4e9797ba479d4d1d9fd2 - 5af424e5adc4970b6e68868204eb3850.png
--------------------------------------

deleting 1 of 9, id=60414bdd2c3a493a8c9a06be82130858 200 OK deleted
deleting 2 of 9, id=2f67c439207a4cb6bcb29068bf21d8fa 200 OK deleted
deleting 3 of 9, id=defd6c6ff6914ca98b960d2170b721ab 200 OK deleted
deleting 4 of 9, id=989b920202a241cbb4dde6c381d6884a 200 OK deleted
deleting 5 of 9, id=2556556e5a0c4b969b0b188154aa4b6d 200 OK deleted
deleting 6 of 9, id=31206111f5a54d97ba312f2257b62c46 200 OK deleted
deleting 7 of 9, id=1765a4bc9db54414968c2d6265683b54 200 OK deleted
deleting 8 of 9, id=0a9b69625f1d4592ad3727f95676074f 200 OK deleted
deleting 9 of 9, id=5c7ec35321dc4e9797ba479d4d1d9fd2 200 OK deleted
Done.
```
