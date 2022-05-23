      
# def scan(self):
#     """
#     Return the dependent files (.sch) by looking in the component library folders.
#     To inspect the scanne results use::

#       $ waf clean build --zones=deps
#     """
#     bld = self.generator.bld
#     found = set()
#     missing = []
#     for sch in self.inputs:
#       Logs.debug(f"deps: -> scanner working with input: {str(sch)}") 

#       syms = read_symbols(sch.abspath())
#       Logs.debug(f"deps: -> scanner found syms : {str(syms)}") 
      
#       sources = read_sources(sch.abspath())
#       if(len(sources)):
#         Logs.debug(f"deps: -> scanner found sources : {str(sources)}") 
      
#       missing += (sources)
#       # sym_srcs = set()
#       for sym in syms:
        
#         idx=None
#         for i, libsym in enumerate(bld.env.sym_ids):
        
#           if(sym == libsym):
#             Logs.debug(f"deps: -> scanner found symbol dependency: {str(sym)}") 
#             idx = i
        
#         if(idx is None):
#           bld.fatal(f"Could not find symbol file: ({str(sym)})")
        
#         sym_path = bld.path.find_resource(bld.env.sym_paths[idx])
#         # sym_srcs.update([sym_path])
#         sym_sources = read_sources(sym_path)
#         if(len(sym_sources) == 0):
#           sym_sources = read_attrs(sym_path, "file")
#         if(len(sym_sources) == 0):
#           bld.fatal("Symbol contains no schematic (with 'source' attribute) or netlist (with 'file' attribute) entries")
          
#         newly_found = set()
#         # FIXME : Add better heuristic for recursive parent sym source search here.
#         for src in sym_sources:
#           Logs.debug(f"deps: -> scanner looking for file : ({str(src)})") 
          
#           result = None
#           path = sym_path.parent
#           while(result is None):
#             Logs.debug(f"deps: -> looking in : ({str(path)})") 
#             result = path.find_node(src)
#             if(path == bld.path):
#               break
#             path = path.parent
            
#           if(result is None):
#             bld.fatal(f"Could not find source file : ({str(src)})")
            
#           newly_found.update([result])
          
#         if(len(newly_found)):
#           Logs.debug(f"deps: -> scanner found sources : {str(newly_found)}") 
#           found.update(newly_found)
          
#       # found += ([bld.path.find_resource(src) for src in sources])
      
#       # if(len(sources) != len(found)):
#       #   bld.fatal("Could not find the sources : %s" % found - sources)
    
#     return (list(found), [])