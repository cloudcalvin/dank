""" DANK Assisted Netlisting Kit
  by Calvin Maree calvin@linuxmail.org
"""
import os
from waflib.Task import Task
from waflib.Configure import conf
from waflib.Scripting import autoconfigure
from waflib.TaskGen import extension, feature, before_method, after_method, taskgen_method
from waflib import Utils, Context, Errors, Logs

NETLIST_EXT = ".js"
SYM_PRE = "mitll_"
LOGFILE = "LOGFILE.log"

def gafrc_lib_string(path, name):
  return f"(component-library {path} {name})"

def gafrc_lib_search_string(path, name):
  return f"(component-library-search {path} {name})"

def gafrc_source_string(path):
  return f"(source {path})"
  
def flatten_recursive(data):
  if isinstance(data, list):
      for x in data:
          yield from flatten_recursive(x)
  else:
      yield data


def init(ctx):
    ctx.load('build_logs')
    ctx.flatten = flatten_recursive
    
def library_opt_handle(ctx, value):
  ctx.env.foo = value
    
def nverbose_handle(ctx, value):
  if(value is not False):
    ctx.env.netlist_verbose = True
  else:
    ctx.env.netlist_verbose = False

def library_search_opt_handle(ctx, value):
  ctx.env.foo = value

def options(ctx):
  ctx.add_option('--nverbose', 
                 action='store', default=False, 
                 help='Netlister verbose', dest="nverbose")
  ctx.add_option('--component-library', 
                 action='store', default=[], 
                 help='Compononent libraries', dest="component_library")
  ctx.add_option('--component-library-search', 
                 action='store', default=[], 
                 help='Component library search paths', dest="component_library_search")
  
  ctx.add_option('--src', action='store', default=False, type='string')
  
def component_lib_configure(ctx):
  """
    Configure the geda/lepton component libraries
  """
  symbols = []
  ctx.add_os_flags('GNET_SYMS')
  ctx.add_os_flags('GNET_SYMS_SEARCH')
  Logs.info(ctx.env.GNET_SYMS)
  Logs.info(ctx.env.GNET_SYMS_SEARCH)
  if(ctx.env.GNET_SYMS):
    for entry in ctx.env.GNET_SYMS:
      node = ctx.path.find_node(entry)
      symbols += node.ant_glob("*.sym")
  
  if(ctx.env.GNET_SYMS_SEARCH):
    Logs.info(ctx.env.GNET_SYMS_SEARCH)
    dirs = flatten_recursive(
      [ctx.path.ant_glob(f"{glob}", dir=True, src=False) 
        for glob in ctx.env.GNET_SYMS_SEARCH])
    
    for d in dirs:
      symbols += d.ant_glob("**/*.sym")
        
  library_opt_handle(ctx, ctx.options.component_library)
  library_search_opt_handle(ctx, ctx.options.component_library_search)
  nverbose_handle(ctx, ctx.options.nverbose)
  
  for i, sym in enumerate(symbols):
    ctx.env.sym_ids += [os.path.basename(sym.abspath())]
    ctx.env.sym_paths += [sym.srcpath()]
    # ctx.env.syms += [sym]
   
  for entry in ctx.env.sym_ids:
    Logs.info(entry)
  
  for entry in ctx.env.sym_paths:
    Logs.info(entry)
    
def configure(ctx):
  """
    Configure the component dank tool/feature
  """
  component_lib_configure(ctx)
  
  ctx.env.NETLISTER = "gnetlist"
  ctx.env.NETLIST_EXT = NETLIST_EXT
  ctx.env.GNET_BACKEND = "spice-sdb"
  ctx.env.GNET_BACKEND_OPTIONS = ['jsim']
  
  ctx.find_program('touch', var='TOUCH')
  if not ctx.env.TOUCH:
    ctx.fatal('could not find the program touch')
  
  ctx.find_program('echo', var='TOUCH')
  if not ctx.env.TOUCH:
    ctx.fatal('could not find the program touch')
    
  try:
    ctx.find_program('gnetlist', var='NETLISTER')
  except ctx.errors.ConfigurationError:
    try:
      ctx.find_program('lepton-netlist', var='NETLISTER')
    except ctx.errors.ConfigurationError:
      ctx.fatal('could not find lepton-netlist or gnetlist')

def read_symbols(sch):
  with open(str(sch), "r") as f:
    lines = map(lambda _: _.strip(), f.readlines())
    syms = [
      line.split(" ")[-1] for line in lines if line.endswith(".sym")
    ]
    return [sym for sym in syms if sym.startswith(SYM_PRE)]

def read_attrs(sch, attr):
  with open(str(sch), "r") as f:
    lines = map(lambda _: _.strip(), f.readlines())
    return [ 
      line.split("=")[1] 
        for line in lines 
          if line.startswith(f"{attr}=")
    ]
    
def read_sources(sch):
  return read_attrs(sch, "source")

def read_files(sch):
  return read_attrs(sch, "file")
    
class netlister(Task):
  vars    = [
    "NETLISTER",
    "GNET_BACKEND",
    "GNET_BACKEND_OPTIONS",
    "VERBOSE"
  ]
  color   = 'BLUE'
  ext_in  = ['.sch']
  ext_out  = [NETLIST_EXT]
  shell = False
 
  def run(self):
    bld = self.generator.bld
    bld.env.netlist_verbose = True
    cmd = f"{bld.env.NETLISTER[0]} \
      {self.inputs[0].get_src()} \
      -g {bld.env.GNET_BACKEND} \
      -O {' '.join(bld.env.GNET_BACKEND_OPTIONS)} \
      -o {self.outputs[0].get_bld()} {'-v' if bld.env.netlist_verbose else ''}"
      
    try:
      # (out, err) 
      out = bld.cmd_and_log(cmd, output=Context.STDOUT, shell=False, cwd=bld.path.get_bld())
      Logs.info(out)
      # if(err):
      #   Logs.error(err)
      return out
    except Errors.WafError as e:
      bld.fatal(e.stdout + e.stderr)
  
  # def runnable_status(self):
  # #   # for t in self.run_after:
  # #   #   if not t.hasrun:
  # #   #     return Task.ASK_LATER
      
  #   ret = super().runnable_status()
  #   bld = self.generator.bld
  #   Logs.info('nodes:       %r' % bld.node_deps[self.uid()])
  #   Logs.info('custom data: %r' % bld.raw_deps[self.uid()])
  #   return ret
  
      
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


  def scan(self):
    """
    Return the dependent files (.sch) by looking in the component library folders.
    To inspect the scanne results use::

      $ waf clean build --zones=deps
    """
    bld = self.generator.bld
    found = set()
    missing = []
    for sch in self.inputs:
      Logs.debug(f"deps: -> scanner working with input: {str(sch)}") 

      syms = read_symbols(sch.abspath())
      Logs.debug(f"deps: -> scanner found syms : {str(syms)}") 
      
      sources = read_sources(sch.abspath())
      if(len(sources)):
        Logs.debug(f"deps: -> scanner found sources : {str(sources)}") 
      
      newly_found = set()
      for src in sources:
        Logs.debug(f"deps: -> scanner looking for file : ({str(src)})") 
        result = None
        path = sch.parent
        while(result is None):
          Logs.debug(f"deps: -> looking in : ({str(path)})") 
          result = path.find_node(src)
          if(path == bld.path):
            break
          path = path.parent
          
        if(result is None):
          bld.fatal(f"Could not find source file : ({str(src)})")
          
        newly_found.update([result])
        
      if(len(newly_found)):
        Logs.debug(f"deps: -> scanner found sources : {str(newly_found)}") 
        found.update(newly_found)
        
      for sym in syms:
        
        idx=None
        for i, libsym in enumerate(bld.env.sym_ids):
        
          if(sym == libsym):
            Logs.debug(f"deps: -> scanner found symbol dependency: {str(sym)}") 
            idx = i
        
        if(idx is None):
          bld.fatal(f"Could not find symbol file: ({str(sym)})")
        
        sym_path = bld.path.find_resource(bld.env.sym_paths[idx])
        found.update([sym_path])
    
    return (list(found), [])

@taskgen_method
def create_netlister_task(self, node):
  """
  :param node: the file to compile
  :type node: :py:class:`waflib.Node.Node`
  :return: The task created
  :rtype: :py:class:`waflib.Task.Task`
  """
  output = node.get_bld().change_ext(self.env.NETLIST_EXT)
  task = self.create_task("netlister", node, output) #node.parent.get_bld().find_or_declare(output))
  try:
    self.compiled_tasks.append(task)
  except AttributeError:
    self.compiled_tasks = [task]
  return task

class copy_task(Task):
  color   = 'PURPLE'
 
  def run(self):
    bld = self.generator.bld
    cmd = f"cp \
      {self.inputs[0].abspath()} \
      {self.outputs[0].abspath()}"
    try:
      return bld.cmd_and_log(cmd, output=Context.STDOUT)
    except Errors.WafError as e:
      Logs.info(e.stdout, e.stderr)
      bld.fatal(e.stderr)

# def find_and_replace_source_line(input):
#   with open(str(input), "r") as f:
#     lines = map(lambda _: _.strip(), f.readlines())
#   with open(str(input), "w") as f:
#     for line in lines:
#       if(line.startswith("source=")):
#         line.replace("source", "file")
#         line.replace(".sch", NETLIST_EXT)
#         f.writeline(line)


class symbol_source_to_file_task(Task):
  color   = 'BLUE'
  ext_in  = ['.sym']
  ext_out  = ['.sym']
  shell = False
  # def copy_sym_file(self):
  #   return self.generator.bld.cmd_and_log(f"cp {self.inputs[0].get_src()} {self.outputs[0].get_bld()}", shell=False)

  # def replace_extension(self):
  #   return self.generator.bld.cmd_and_log(f"sed -n '/source=/ s/.sch/{NETLIST_EXT}/gp' {self.outputs[0].abspath()}", shell=False)

  # def rename_attribute(self):
  #   return self.generator.bld.cmd_and_log(f"sed -n '/source=/ s/source/file/gp'  {self.outputs[0].abspath()}", shell=False)

  # run_str = (copy_sym_file, replace_extension, rename_attribute)
  
  def run(self):
    bld = self.generator.bld
    cmd = f"cat {self.inputs[0].abspath()} \
          | sed -e '/source=/ s/.sch/{NETLIST_EXT}/g' -e '/source=/ s/source/file/g' \
          > {self.outputs[0].abspath()}"
          
    try:
      return bld.cmd_and_log(cmd, output=Context.STDOUT)
    except Errors.WafError as e:
      Logs.info(e.stdout, e.stderr)
      bld.fatal(e.stderr)
  
  # def run(self):
  #   bld = self.generator.bld
  #   self.inputs[0].abspath()
  #   cmd = f"cp {self.inputs[0].get_src()} {self.outputs[0].get_bld()} \
  #           && sed -n '/source=/ s/.sch/{NETLIST_EXT}/gp' {self.outputs[0].abspath()} \
  #           && sed -n '/source=/ s/source/file/gp'  {self.outputs[0].abspath()}"
  #   try:
  #     return bld.cmd_and_log(cmd, output=Context.STDOUT)
  #   except Errors.WafError as e:
  #     Logs.info(e.stdout, e.stderr)
  #     bld.fatal(e.stderr)
      
  # def scan(self):
  #   bld = self.generator.bld
  #   found = set()
  #   for sym in self.inputs:
  #     sym_sources = read_sources(sym)
  #     if(len(sym_sources) == 0):
  #       sym_sources = read_attrs(sym, "file")
  #     if(len(sym_sources) == 0):
  #       bld.fatal("Symbol contains no schematic (with 'source' attribute) or netlist (with 'file' attribute) entries")
        
  #     newly_found = set()
  #     # FIXME : Add better heuristic for recursive parent sym source search here.
  #     for src in sym_sources:
  #       Logs.debug(f"deps: -> scanner looking for file : ({str(src)})") 
        
  #       result = None
  #       path = sym.parent
  #       while(result is None):
  #         Logs.debug(f"deps: -> looking in : ({str(path)})") 
  #         result = path.find_node(src)
  #         if(path == bld.path):
  #           break
  #         path = path.parent
          
  #       if(result is None):
  #         bld.fatal(f"Could not find source file : ({str(src)})")
          
  #       newly_found.update([result])
        
  #     if(len(newly_found)):
  #       Logs.debug(f"deps: -> scanner found sources : {str(newly_found)}") 
  #       found.update(newly_found)
        
  #   return (list(found), [])
# class find_and_replace_task(self):
#   def run(self):
#     bld = self.generator.bld
#     cmd = f"sed s/\
#       {self.inputs[0].abspath()} \
#       {self.outputs[0].abspath()} \
#       /g "
#     try:
#       return bld.cmd_and_log(cmd, output=Context.STDOUT)
#     except Errors.WafError as e:
#       Logs.info(e.stdout, e.stderr)
#       bld.fatal(e.stderr)
# @taskgen_method
# def create_netlist_copy_task(self, node):
#   """
#   :param node: the file to compile
#   :type node: :py:class:`waflib.Node.Node`
#   :return: The task created
#   :rtype: :py:class:`waflib.Task.Task`
#   """
#   output = node.get_bld().change_ext(self.env.NETLIST_EXT)
#   task = self.create_task("copy_task", node, output) #node.parent.get_bld().find_or_declare(output))
#   try:
#     self.compiled_tasks.append(task)
#   except AttributeError:
#     self.compiled_tasks = [task]
#   return task

# @taskgen_method
# def create_symbol_copy_task(self, node):
#   """
#   :param node: the file to compile
#   :type node: :py:class:`waflib.Node.Node`
#   :return: The task created
#   :rtype: :py:class:`waflib.Task.Task`
#   """
#   output = node.get_bld().change_ext(self.env.NETLIST_EXT)
#   task = self.create_task("copy_task", node, output) #node.parent.get_bld().find_or_declare(output))
#   try:
#     self.compiled_tasks.append(task)
#   except AttributeError:
#     self.compiled_tasks = [task]
#   return task

@extension('.sch')
def sch_hook(self, node):
  """Binds the sch file extensions to task instances"""
  if not self.env.DANK:
    self.bld.fatal("use dank method to compile project files")
  return self.create_netlister_task(node)

@extension(NETLIST_EXT)
def netlist_hook(self, node):
  """Binds the netlist file extensions to a task instances"""
  if not self.env.DANK:
    self.bld.fatal("use dank method to compile project files")
  output = node.get_bld().change_ext(self.env.NETLIST_EXT)
  task = self.create_task("copy_task", node, output)
  return task


@extension(".sym")
def symbol_hook(self, node):
  """Binds the symbol file extensions to a task instances"""
  if not self.env.DANK:
    self.bld.fatal("use dank method to compile project files")
  output = node.get_bld().change_ext(".sym")
  task = self.create_task("symbol_source_to_file_task", node, output)
  return task


@feature("dank")
def dummy(task):
  pass

# @conf
# def netlist(bld, *k, **kw):
#   """
#   Compile a netlist from a schematic file::

#     def build(bld):
#       bld.compile(source='foo.sch')

#   """
#   kw["features"] = 'dank'
#   bld.env.DANK = True
#   return bld(*k, **kw)

@conf
# @before_method('process_source', 'process_rule')
def dank(self, srcs, excl, flag_extra, *k, **kw):
  self.env.DANK = True
  
#   # Utils.def_attrs(self, jarname='', classpath='',
#   #   sourcepath='.', srcdir='.',
#   #   jar_mf_attributes={}, jar_mf_classpath=[])
  
  # configs = [
  #   self.path.find_resource("gschemrc"),
  
  configs = [ conf for conf in [
      self.path.find_resource("gafrc"),
      self.path.find_resource("gschemrc"),
      *self.path.ant_glob("lepton*.conf")
    ] if conf is not None]
  # self(rule='touch ${TGT}', target='.root')
  # self(rule='echo %s > ${TGT}' % , target="gafrc.template")
  # self(rule='ROOT=%s envsubst < ${SRC} > ${TGT}' % self.path, 
  #   source='gafrc.template', 
  #   target='gafrc')
  for conf in configs:
    self(rule="cp ${SRC} ${TGT}", source=conf.get_src(), target=conf.get_bld(), shell=False)
    
  # self(rule="sed --help")
  for sym_path in self.env.sym_paths:
    sym = self.path.find_node(sym_path).get_src()
    self(source=sym, shell=False, *k, **kw)
    
  if(self.options.src):
    Logs.info(self.path)
    src = self.path.find_node(self.options.src)
    if(src is None):
      self.fatal("source not found")
    Logs.info("only compiling sources : [%s]" % ([src]))
    self(source = src, shell=False, *k, **kw)
  else:
    source_dirs = flatten_recursive(
      [self.path.ant_glob(f"{glob}", dir=True, src=False) 
        for glob in srcs])
  
    for d in source_dirs:
      all_sch_srcs = d.ant_glob("*.sch")
      all_nl_srcs = d.ant_glob(f"*{self.env.NETLIST_EXT}")
      tb_sch_srcs = d.ant_glob("tb_*.sch") + \
        d.ant_glob("test_*.sch") 
      tb_nl_srcs = d.ant_glob(f"test_*{self.env.NETLIST_EXT}") + \
        d.ant_glob(f"test_*{self.env.NETLIST_EXT}")
            
      non_tb_sch_srcs = set(all_sch_srcs) - set(tb_sch_srcs)
      non_tb_nl_srcs = set(all_nl_srcs) - set(tb_nl_srcs)
      
      final_sources = non_tb_sch_srcs
      
      for src in non_tb_nl_srcs:
        if(src.change_ext('.sch').get_src() not in list(final_sources)):
          final_sources.update([src])
          
      for src in final_sources:
        self(source = src, shell=False, *k, **kw)
    # return self()

@autoconfigure
def debug(bld):
  if(not bld.options.src):
    bld.fatal("debug requires the --src flag")
  bld(bld.options.src) 
  
from waflib.Build import BuildContext
class debug_command(BuildContext):
  cmd = 'debug'
  variant = 'debug'
