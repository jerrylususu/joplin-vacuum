from urllib import request
import tarfile
import argparse
import json
from pathlib import Path

JOPLIN_PORT_RANGE = (41184, 41194)
JOPLIN_PING_RESPONSE = "JoplinClipperServer"
JOPLIN_RESOURCES_PATH = "resources/"
JOPLIN_RESOURCE_ID_LEN = 32

def get_joplin_port():
    for port in range(*JOPLIN_PORT_RANGE):
        print("trying port", port, end=" ")
        req = request.Request(f"http://localhost:{port}/ping")
        try:
            with request.urlopen(req) as f:
                print(f.status, f.reason, end=" ")
                if f.status == 200 and f.read().decode("utf-8") == JOPLIN_PING_RESPONSE:
                    print("port find!")
                    return port
        except Exception as e:
            print("not the port, skipping")

    print("port not found")
    return None

def auth(port, provided_token = None):
    if provided_token is not None:
        print("using provided token")
        return provided_token

    if Path(".joplin_token").exists():
        with open(".joplin_token","r",encoding="utf8") as f:
            resp = json.load(f)
            print("loading token from file")
            return resp["token"]

    print("no existing token found, requesting")
    req = request.Request(f"http://localhost:{port}/auth")
    with request.urlopen(req, data=b"") as f:
        print(f.status, f.reason)
        if f.status == 200:
            resp = json.loads(f.read().decode("utf-8"))
            print("Token requested. Please check the joplin app to grant access.")
            input("Press enter after granting access.")
    
    token = resp["auth_token"]

    req = request.Request(f"http://localhost:{port}/auth/check?auth_token={token}")
    with request.urlopen(req) as f:
        print(f.status, f.reason)
        if f.status == 200:
            resp = json.loads(f.read().decode("utf-8"))
            print(resp)
            if resp["status"] == "accepted":
                print("auth success!")

    with open(".joplin_token","w",encoding="utf8") as f:
        print("saving token to file")
        json.dump(resp, f)

    return resp["token"]

def get_joplin_resources(port, token, limit):
    has_more = True
    resources = []
    page = 1

    # set default
    if limit is None or not 0 < limit and limit <= 100:
        limit = 50

    while has_more:
        print(f"requesting page {page}...", end=" ")
        req = request.Request(f"http://localhost:{port}/resources?token={token}&limit={limit}&page={page}")
        
        with request.urlopen(req) as f:
            print(f.status, f.reason, end=" ")
            if f.status == 200:
                resp = json.loads(f.read().decode("utf-8"))
                # print(resp)
        resources += resp["items"]
        has_more = resp["has_more"]
        page += 1
        print(f"got {len(resp['items'])}, total {len(resources)}, has_more {has_more}")

    return resources

def read_jex_resources(jex_path):
    with tarfile.open(jex_path, "r") as f:
        files = f.getmembers()
    
    resources = [f.name.replace(JOPLIN_RESOURCES_PATH,"")[:JOPLIN_RESOURCE_ID_LEN] 
                for f in files if f.name.startswith(JOPLIN_RESOURCES_PATH)]

    return resources

def diff(referred, all):
    all_id_to_title_dict = {item["id"]:item["title"] for item in all}

    referred_set = set(referred)
    all_set = set(all_id_to_title_dict.keys())

    referred_subsets_all = referred_set.issubset(all_set)
    if not referred_subsets_all:
        raise Exception("Sanity check failed: referred ids is not a subset of all attachment ids!")

    not_referred = set(all_set).difference(referred_set)

    print("orphaned count:", len(not_referred))
    print("")

    print("id - filename")
    print("--------------------------------------")
    for id in not_referred:
        print(f"{id} - {all_id_to_title_dict[id]}")
    print("--------------------------------------")
    print()

    return not_referred

def do_delete(not_referred, port,token):
    not_referred_len = len(not_referred)
    for idx, id in enumerate(not_referred):
        print(f"deleting {idx+1} of {not_referred_len}, id={id}", end=" ")
        req = request.Request(f"http://localhost:{port}/resources/{id}?token={token}", method="DELETE")
        
        with request.urlopen(req) as f:
            print(f.status, f.reason, end=" ")
            if f.status == 200:
                print("deleted")
            else:
                raise Exception("deletion failed, exiting...")


def main(args):
    port = args.port

    if not port:
        port = get_joplin_port()
        if port is None:
            raise Exception("failed to connect to joplin port...")

    token = args.token
    
    if not token:
        token = auth(port)
        if token is None:
            raise Exception("failed to obtain joplin API token...")

    referred = read_jex_resources(args.jex_path)
    all = get_joplin_resources(port, token, limit=args.limit)

    print(f"referred: {len(referred)}, all {len(all)}")

    not_referred = diff(referred, all)

    if len(not_referred) == 0:
        print("No need to vacuum.")
        return

    if not args.confirm:
        print('Confirm flag (--confirm) not set. Exiting without any deletion.')
        return

    if args.test_del_1:
        to_be_removed = [list(not_referred)[0]]
    else:
        to_be_removed = list(not_referred)

    do_delete(to_be_removed, port, token)

    print("Done.")

if __name__ == "__main__":

    description = """
Joplin Vacuum Cleaner

Removes attachments that are not referred. 

!!! Always backup before using this tool and use at your own risk. !!!

Before using the script, you need to export your notes as a JEX file (Joplin Export File). The process of exporting 
notes checks the reference of attachments, and attachments that are no longer referenced is not exported. The script
works out attachments not referred by calculating attachment ids that appears in Joplin Note Attachment Panel but 
not in the exported file.

By default, only a list of not referred attachments are generated (i.e. dryrun). No deletion will take place unless
"confirm" flag is set ("--confirm").

For the first run, the script will request an API token from Joplin. The token will be store in the ".joplin_token"
file under the same directory as the script. Subsequent requests will reuse the token.
"""

    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("jex_path", type=str, help="Path to the JEX file")
    parser.add_argument("--port", type=int, default=None, help="the port used to connect to Joplin, leave blank for auto query")
    parser.add_argument("--token", type=str, default=None, help="override API token")
    parser.add_argument("--limit", type=int, default=50, help="pagenation limit for querying attachments from Joplin")
    parser.add_argument("--confirm", action='store_true', help="Confirm deletion")
    parser.add_argument("--test-del-1",action='store_true', help="(For testing purpose) Removing one not referred attachment. Need to be used with confirm.")

    args = parser.parse_args()

    main(args)
