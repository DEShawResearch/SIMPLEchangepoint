import os, platform
import py_compile

from SCons.Script import *

ActionFactory = SCons.Action.ActionFactory

EnsurePythonVersion(2,4)
EnsureSConsVersion(1,2)

def handle_external_libs(env, kwds):
  ''' Append EXTERNAL_LIBS onto env[LIBS] and kwds[LIBS].  '''
  key='EXTERNAL_LIBS'
  if key in env:
    env.AppendUnique(LIBS=env[key])
  if key in kwds:
    kwds.setdefault('LIBS',[]).extend(kwds[key])

def _AddPlugin(env, name, *args, **kwds):
    kwds.update(LIBPREFIX='', LDMODULESUFFIX='.so')
    env=env.Clone()
    env.Replace(LIBS=[])
    handle_external_libs(env,kwds)
    if platform.system()=='Darwin':
        env.AppendUnique( LINKFLAGS=['-undefined','dynamic_lookup'] )
    lib=env.LoadableModule('$OBJDIR/lib/plugin/%s' % name, *args, **kwds)
    if env['PREFIX'] is not None:
        tgt='$PREFIX/lib/plugin'
        env.Install(tgt, lib)
        env.Alias('install', tgt)
    return lib

def _AddMolfilePlugin(env, name, *args, **kwds):
    kwds.update(LIBPREFIX='')
    lib=env.LoadableModule('$OBJDIR/lib/molfile/%s' % name, *args, **kwds)
    if env['PREFIX'] is not None:
        tgt='$PREFIX/lib/molfile'
        env.Install(tgt, lib)
        env.Alias('install', tgt)
    return lib

def _AddPythonExtension(env, name, *args, **kwds):
    env=env.Clone()
    handle_external_libs(env,kwds)
    kwds.update(LIBPREFIX='')
    prefix=kwds.get('prefix', '')
    py='$OBJDIR/lib/python/%s/%s' % (prefix, name)
    lib=env.LoadableModule(py, *args, **kwds)
    if env['PREFIX'] is not None:
        tgt=os.path.join(env['PREFIX'], 'lib', 'python', prefix)
        env.Install(tgt, lib)
        env.Alias('install', tgt)
    return lib

def _AddLibrary(env, name, *args, **kwds):
    if not isinstance(name, str):
        raise ValueError, "AddLibrary: expected name to be string, got %s" % type(name)
    if 'archive' in kwds and kwds['archive']:
        lib=env.Library( '$OBJDIR/lib/%s' % name, *args, **kwds)
    else:
        lib=env.SharedLibrary( '$OBJDIR/lib/%s' % name, *args, **kwds)
    # install
    if env.get('PREFIX') is not None:
        tgt='$PREFIX/lib'
        env.Install(tgt, lib)
        env.Alias('install', tgt)
    return lib

## def _AddProgram(env, name, *args, **kwds):
##     env=env.Clone()
##     handle_external_libs(env,kwds)
##     prog=env.Program('$OBJDIR/bin/%s' % name, *args, **kwds)
##     if env.get('PREFIX') is not None:
##         tgt='$PREFIX/bin'
##         env.Install(tgt, prog)
##         env.Alias('install', tgt)
##     return prog

def _AddProgram(env, name, *args, **kwds):
    return []

def _AddExecutable(env, name, *args, **kwds):
    env=env.Clone()
    handle_external_libs(env,kwds)
    env.AppendUnique(LIBS=env.get('DESRES_LIBS', []))
    prog=env.Program(name, *args, **kwds)
    return prog

def _AddUnitTest(env, name, *args, **kwds):
    env=env.Clone()
    handle_external_libs(env,kwds)
    env.AppendUnique(LIBS=env.get('DESRES_LIBS', []))
    prog=env.Program('$OBJDIR/unit-tests/%s' % name, *args, **kwds)
    alias=env.Alias('test', [prog], prog[0].path)
    env.AlwaysBuild(alias)
    return prog

## def _AddScriptUnitTest(env, name, src=None):
##     if src is None: src=name
##     name=os.path.basename(name)
##     prog=env.Command('$OBJDIR/unit-tests/%s'%name, src, [
##         Delete("$TARGET"),
##         Copy("$TARGET", "$SOURCE"),
##         Chmod("$TARGET", 0755)])
##     alias=env.Alias('test', [prog], prog[0].path)
##     env.AlwaysBuild(alias)
##     return prog

def _AddScriptUnitTest(env, name, src=None):
    return []

def _AddShare( env, name, src=None ):
  if src is None: src=name
  if os.path.isabs(name):
      raise ValueError, "AddShare: name='%s' cannot be an absolute path"%name
  prog=env.Command('$OBJDIR/share/%s'%name, src, [
      Delete("$TARGET"),
      Copy("$TARGET", "$SOURCE") ])

  if env.get('PREFIX') is not None:
    tgt=os.path.join(env['PREFIX'], 'share')
    env.InstallAs(os.path.join(tgt, name), src)
    env.Alias('install', tgt)
  return prog 

## def _AddScript( env, name, src=None ):
##   if src is None: src=name
##   name=os.path.basename(name)
##   prog=env.Command('$OBJDIR/bin/%s'%name, src, [
##       Delete("$TARGET"),
##       Copy("$TARGET", "$SOURCE"),
##       Chmod("$TARGET", 0755)])

##   if env.get('PREFIX') is not None:
##     tgt=os.path.join(env['PREFIX'], 'bin')
##     env.InstallAs(os.path.join(tgt, name), prog)
##     env.Alias('install', tgt)
##   return prog 

def _AddScript( env, name, src=None ):
  return []

def python_compile_func( dst, src ):
    import py_compile
    py_compile.compile( src, dst )

def python_compile_strfunc( dst, src ):
    return "%s->%s" % (src,dst)

PyCompile=ActionFactory(python_compile_func, python_compile_strfunc)

def _AddPythonModule( env, *args, **kwds ):
    ''' Install python files $args into lib/python.
    Optional prefix keyword argument puts files into lib/python/$prefix/.
    '''
    prefix=kwds.get('prefix', '')
    progs=[]
    for s in args:
        py='$OBJDIR/lib/python/%s/%s' % (prefix, os.path.basename(s))
        pyc=py+'c'
        progs.extend( env.Command(py, s, Copy("$TARGET", "$SOURCE" )))
        progs.extend( env.Command(pyc, s, PyCompile( "$TARGET", "$SOURCE" )))

    if env.get('PREFIX') is not None:
        tgt=os.path.join(env['PREFIX'], 'lib', 'python', prefix)
        env.Install(tgt, progs)
        env.Alias('install', tgt)

    return progs

def _AddHeaders( env, names, prefix='' ):
  if env['PREFIX'] is not None:
    tgt=os.path.join(env['PREFIX'], 'include', prefix)
    prog=env.Install(tgt,names)
    env.Alias('install', tgt)
    return prog
  return None

# FIXME: could we possibly add this as an option for AddHeaders maybe?
def _AddStagedHeaders( env, names, prefix='' ):
    for n in names: 
        tgt = '$OBJDIR/include/%s/%s' % (prefix, os.path.basename(str(n)))
        env.Command( tgt, n, Copy("$TARGET", "$SOURCE") )
    return _AddHeaders( env, names, prefix )

def _AddShareFiles( env, names, prefix='' ):
  if env.get('PREFIX') is not None:
    tgt=os.path.join(env['PREFIX'], 'share', prefix)
    prog=env.Install(tgt,names)
    env.Alias('install', tgt)
    return prog
  return None

def _AddObject(env, *args, **kwds):
    return env.SharedObject(*args, **kwds)

def _AddDoxygen( env, doxyfile ):
    target = os.path.join(env['OBJDIR'], 'share', 'doxygen')
    source = doxyfile
    commands = [
        '(cat $SOURCES && echo OUTPUT_DIRECTORY=$TARGET) | doxygen -',
        ]
    prog = env.Command(target, source, commands)
    env.Clean(target, target)
    if env.get('PREFIX') is not None:
        ret = env.InstallAs('$PREFIX/share/doc',target)
        env.Alias('install', ret)
    return prog

def _AddWisp( env, module, cxxfile, source ):
    env = env.Clone()
    handle_external_libs(env,dict())
    env.AppendUnique(CPPPATH='.')
    cxx = os.path.join(env['OBJDIR'], cxxfile)
    commands = [
        "wisp --cppflags='$CXXFLAGS $CCFLAGS $_CCCOMCOM' --cxxflags='' --module %s --output $TARGET $SOURCES"%(module),
        ]
    prog = env.Command(cxx, source, commands)
    env.Clean(cxx, cxx)
    return env.AddPythonExtension(module, cxx)

def Customize( env ):

    desres_os  = os.getenv("DESRES_OS",  platform.system())
    desres_isa = os.getenv("DESRES_ISA", platform.machine())
    # this cannot come in any other way.  Don't change. -RAL
    desres_bc = os.getenv("BUILDCLASS", None)

    if desres_isa == '' and desres_os == 'Windows':
        desres_isa = os.getenv('PROCESSOR_ARCHITECTURE')

    opts=Variables()
    # Allow PREFIX to be set on the command line
    opts.Add("PREFIX", "installation location")
    # Allow OBJDIR to be set on the command line
    opts.Add("OBJDIR", "build product location")
    opts.Update(env)

    # Construct OBJDIR if not provided
    if env.get('OBJDIR') is None:
        # Construct OBJDIR = #objs/$DESRES_OS/$DESRES_ISA
        objdir = os.path.join( '#objs', desres_os, desres_isa )

        # Add /$BUILDCLASS if provided
        if desres_bc is not None:
            objdir += '/%s' % desres_bc
        env['OBJDIR'] = objdir

    # Set env vars.
    env['ENV']['PATH'] = os.getenv('PATH')
    env['DESRES_OS'] = desres_os
    env['DESRES_ISA'] = desres_isa
    env['BUILDCLASS'] = desres_bc

    env['CONFIGUREDIR']='$OBJDIR/config.tmp'
    env['CONFIGURELOG']='$OBJDIR/config.log'
    env.SetDefault(PREFIX=None)

    env.Prepend( CPPPATH=['$OBJDIR/include'] )
    env.AppendUnique( LIBPATH=['$OBJDIR/lib'] )
    env.AppendUnique( RPATH=[
        env.Literal('\\$$ORIGIN/../lib'), # bins link to libs
        env.Literal('\\$$ORIGIN/../../lib'), # python extensions to libs
        env.Literal('\\$$ORIGIN/../../../lib')] ) # more python exts to libs
    if desres_os == 'Linux':
        env.AppendUnique( LINKFLAGS = Split('-z origin') )

    # Import compile flags
    for key in ( 'DESRES_MODULE_CPPFLAGS', 
                 'DESRES_MODULE_LDFLAGS',
                 'DESRES_MODULE_LDLIBS'):
        d=env.ParseFlags(' '.join(os.getenv(key,'').split(':')))
        env.MergeFlags(d)

    # CFLAGS and CXXFLAGS don't always get interpreted by SCons in the
    # right way (DESRESCode#1123).  Make sure the CFLAGS and CXXFLAGS
    # parts end up in the right place.
    for src, dst in (
            ('DESRES_MODULE_CFLAGS',    'CFLAGS'),
            ('DESRES_MODULE_CXXFLAGS',  'CXXFLAGS')):
        d=env.ParseFlags(' '.join(os.getenv(src,'').split(':')))
        if dst in d:
            v=d.pop(dst, None)
            if v is not None:
                env.Append(**{dst:v})
        env.MergeFlags(d)

    # Add the builders
    for name, func in globals().items():
        if name.startswith('_Add') and callable(func):
            name=name[1:]
            env.AddMethod( func, name )

    # Preserve the original AddScript in case someone wants to override
    # AddScript while still providing a way to use the original version.
    env.AddDesresScript = env.AddScript

def build():
    env = Environment(ENV=os.environ)
    Customize(env)
    Export('env')
    SConscript('SConscript', variant_dir=env['OBJDIR'], duplicate=0)
