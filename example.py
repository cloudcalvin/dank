# top = '.'
# out = 'build'

dank_url="<this locally downloaded repo path>"

# 1	Load the options defined in dang.py
def options(ctx):
    ctx.load('dank', tooldir=dank_url)

# 2	Load the tool dang.py. By default, load calls the method configure defined in the tools.
def configure(ctx):
    ctx.load('dank', tooldir=dank_url)

# 3	The tool modifies the value of ctx.env.DANG during the configuration 
def build(ctx):
    print(ctx.env.DANK)
    ctx.dank('src')

