# def find_and_replace_source_line(input):
#   with open(str(input), "r") as f:
#     lines = map(lambda _: _.strip(), f.readlines())
#   with open(str(input), "w") as f:
#     for line in lines:
#       if(line.startswith("source=")):
#         line.replace("source", "file")
#         line.replace(".sch", NETLIST_EXT)
#         f.writeline(line)