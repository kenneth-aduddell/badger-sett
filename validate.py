#!/usr/bin/env python3
import json
import sys

from collections import defaultdict

import colorama
import tldextract

# ./validate.py old.json new.json
if len(sys.argv) == 3:
    old_path = sys.argv[1]
    new_path = sys.argv[2]
# ./validate.py new.json
elif len(sys.argv) == 2:
    old_path = None
    new_path = sys.argv[1]
else:
    print("Usage: {} [BADGER_JSON_OLD] BADGER_JSON_NEW".format(sys.argv[0]))
    sys.exit(1)

if old_path:
    with open(old_path) as f:
        old_js = json.load(f)
else:
    old_js = {
        "action_map": {},
        "snitch_map": {},
    }

with open(new_path) as f:
    new_js = json.load(f)

# make sure new JSON is not the same as old JSON
assert old_js != new_js

# make sure the JSON is structured correctly
for k in ['action_map', 'snitch_map']:
    assert k in new_js

# make sure there is data in the maps
if not new_js['snitch_map'].keys():
    print("Error: Snitch map empty.")
    sys.exit(1)

if not new_js['action_map'].keys():
    print("Error: Action map empty.")
    sys.exit(1)

old_keys = set(old_js['action_map'].keys())
new_keys = set(new_js['action_map'].keys())

overlap = old_keys & new_keys
print("New action map has %d new domains and dropped %d old domains" %
      (len(new_keys - overlap), len(old_keys - overlap)))

colorama.init()
C_GREEN = colorama.Style.BRIGHT + colorama.Fore.GREEN
C_RED = colorama.Style.BRIGHT + colorama.Fore.RED
C_RESET = colorama.Style.RESET_ALL

extract = tldextract.TLDExtract(cache_file=False)

BLOCKED = ("block", "cookieblock")

blocked_old = defaultdict(list)
for domain in old_js['action_map'].keys():
    if old_js['action_map'][domain]['heuristicAction'] not in BLOCKED:
        continue

    base = extract(domain).registered_domain
    blocked_old[base].append(domain)

blocked_new = defaultdict(list)
for domain in new_js['action_map'].keys():
    if new_js['action_map'][domain]['heuristicAction'] not in BLOCKED:
        continue

    base = extract(domain).registered_domain
    blocked_new[base].append(domain)

blocked_bases_old = set(blocked_old.keys())
blocked_bases_new = set(blocked_new.keys())

if blocked_bases_old:
    print("\nCount of blocked base domains went from {} to {} ({:+0.2f}%)".format(
        len(blocked_bases_old), len(blocked_bases_new),
        (len(blocked_bases_new) - len(blocked_bases_old)) / len(blocked_bases_old) * 100
    ))

newly_blocked = blocked_bases_new - blocked_bases_old
print("\n{}++{} Newly blocked domains ({}):\n".format(
    C_GREEN, C_RESET, len(newly_blocked)))
for base in sorted(newly_blocked):
    subdomains = blocked_new[base]
    out = "  {}{}{}".format(C_GREEN, base, C_RESET)
    if base in new_js['snitch_map']:
        out = out + " on " + ", ".join(new_js['snitch_map'][base])
    print(out)
    if len(subdomains) > 1 or subdomains[0] != base:
        for y in sorted(subdomains):
            if y == base:
                continue
            out = "    • {}"
            if y in new_js['snitch_map']:
                out = out + " on " + ", ".join(new_js['snitch_map'][y])
            print(out.format(y))

no_longer_blocked = blocked_bases_old - blocked_bases_new
print("\n{}--{} No longer blocked domains ({}):\n".format(
    C_RED, C_RESET, len(no_longer_blocked)))
for base in sorted(no_longer_blocked):
    subdomains = blocked_old[base]
    out = "  {}{}{}".format(C_RED, base, C_RESET)
    if base in old_js['snitch_map']:
        out = out + " on " + ", ".join(old_js['snitch_map'][base])
    print(out)
    if len(subdomains) > 1 or subdomains[0] != base:
        for y in sorted(subdomains):
            if y == base:
                continue
            out = "    • {}"
            if y in old_js['snitch_map']:
                out = out + " on " + ", ".join(old_js['snitch_map'][y])
            print(out.format(y))

print("")

sys.exit(0)
