import argparse
parser = argparse.ArgumentParser()

parser.add_argument("--mode", choices=["add", "search", "delete"], required=True, help="Memory operation")

args = parser.parse_args()

if args.mode == "add":
    print("Adding")

elif args.mode == "search":
    print("Searching")

elif args.mode == "delete":
    print("Deleting")