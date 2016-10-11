#
# Collective Knowledge (os)
#
# See CK LICENSE.txt for licensing details
# See CK COPYRIGHT.txt for copyright details
#
# Developer: Grigori Fursin, Grigori.Fursin@cTuning.org, http://fursin.net
#

cfg={}  # Will be updated by CK (meta description of this module)
work={} # Will be updated by CK (temporal data)
ck=None # Will be updated by CK (initialized CK kernel) 

# Local settings

##############################################################################
# Initialize module

def init(i):
    """

    Input:  {}

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """
    return {'return':0}

##############################################################################
# find close OS

def find_close(i):
    """
    Input:  {
              (os_uoa)     - load info from a given OS
              (os_dict)    - if non-empty, return this dict
            }

    Output: {
              return     - return code =  0

              platform   - 'win' or 'linux'. Careful - it is always for current host OS! 
                           Use 'ck_name' key from meta for the target OS!

              bits       - (str) 32 or 64. Careful - it is always for current host OS!
                           Use 'bits' key from meta for the target OS!

              os_uoa     - UOA of the most close OS
              os_uid     - UID of the most close OS
              os_dict    - meta of the most close OS

              (add_path) - list of extra path ...
            }
    """

    r=ck.get_os_ck({})
    if r['return']>0: return r

    bits=r['bits']
    plat=r['platform']

    xos=i.get('os_uoa','')
    fc=i.get('find_close','')

    if xos=='':
       # Detect host platform
       # Search the most close OS
       ii={'action':'search',
           'module_uoa':work['self_module_uid'],
           'search_dict':{'ck_name':plat,
                          'bits':bits,
                          'generic':'yes',
                          'priority':'yes'},
           'internal':'yes'}

       # Adding extra tags to separate different Linux flavours such as Mac OS X:
       import sys
       pl=sys.platform

       if pl=='darwin':
          ii['tags']='macos'
       elif plat=='linux':
          ii['tags']='standard'

       rx=ck.access(ii)
       if rx['return']>0: return rx

       lst=rx['lst']
       if len(lst)==0:
          return {'return':0, 'error':'most close platform was not found in CK'}

       pl=lst[0]

       xos=pl.get('data_uoa','')

    rr={'return':0, 'platform':plat, 'bits':bits}

    # Load OS
    if xos!='':
       r=ck.access({'action':'load',
                    'module_uoa':'os', 
                    'data_uoa':xos})
       if r['return']>0: return r

       os_uoa=r['data_uoa']
       os_uid=r['data_uid']

       dd=r['dict']

       if len(i.get('os_dict',{}))!=0: # Substitute from 'machine' description (useful for remote access)
           dd=i['os_dict']

       rr['os_uoa']=os_uoa
       rr['os_uid']=os_uid
       rr['os_dict']=dd

       # Check if need to add path
       x=dd.get('add_to_path_os_uoa','')
       if x!='':
          rx=ck.access({'action':'find',
                        'module_uoa':work['self_module_uid'],
                        'data_uoa':x})
          if rx['return']>0: return rx
          px=rx['path']

          rr['add_path']=[px]

    return rr

##############################################################################
# shell in OS

def shell(i):
    """
    Input:  {
              (target)
              (host_os)
              (target_os)
              (device_id)

              (cmd) -           cmd string (can have \n)

              (split_to_list) - if 'yes', split stdout and stderr to list
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              return_code

              stdout or stdout_lst
              stderr or stderr_lst
            }

    """

    import os

    o=i.get('out','')
    oo=''
    if o=='con': oo='con'

    stl=i.get('split_to_list','')

    # Check if need to initialize device and directly update input i !
    ii={'action':'init',
        'module_uoa':cfg['module_deps']['machine'],
        'input':i}
    r=ck.access(ii)
    if r['return']>0: return r

    device_cfg=i.get('device_cfg',{})

    # Check host/target OS/CPU
    hos=i.get('host_os','')
    tos=i.get('target_os','')
    tdid=i.get('device_id','')

    # Get some info about platforms
    ii={'action':'detect',
        'module_uoa':cfg['module_deps']['platform.os'],
        'host_os':hos,
        'target_os':tos,
        'device_cfg':device_cfg,
        'device_id':tdid,
        'skip_info_collection':'yes'}
    r=ck.access(ii)
    if r['return']>0: return r

    hos=r['host_os_uid']
    hosx=r['host_os_uoa']
    hosd=r['host_os_dict']

    tos=r['os_uid']
    tosx=r['os_uoa']
    tosd=r['os_dict']

    tdid=i.get('device_id','')

    xtdid=''
    if tdid!='': xtdid=' -s '+tdid

    envsep=hosd.get('env_separator','')
    sext=hosd.get('script_ext','')
    sexe=hosd.get('set_executable','')
    sbp=hosd.get('bin_prefix','')
    scall=hosd.get('env_call','')
    ubtr=hosd.get('use_bash_to_run','')
    stro=tosd.get('redirect_stdout','')
    stre=tosd.get('redirect_stderr','')

    cmd=i.get('cmd','')

    # Tmp file for stdout
    rx=ck.gen_tmp_file({'prefix':'tmp-', 'suffix':'.tmp', 'remove_dir':'no'})
    if rx['return']>0: return rx
    fno=rx['file_name']

    # Tmp file for stderr
    rx=ck.gen_tmp_file({'prefix':'tmp-', 'suffix':'.tmp', 'remove_dir':'no'})
    if rx['return']>0: return rx
    fne=rx['file_name']

    # Check remote shell
    rs=tosd.get('remote_shell','')
    if rs!='':
        # ADB dependency
        deps={'adb':{
                     "force_target_as_host": "yes",
                     "local": "yes", 
                     "name": "adb tool", 
                     "sort": -10, 
                     "tags": "tool,adb"
                     }
             }

        ii={'action':'resolve',
            'module_uoa':cfg['module_deps']['env'],
            'host_os':hos,
            'target_os':tos,
            'device_id':tdid,
            'deps':deps,
            'add_customize':'yes',
            'out':oo}
        rx=ck.access(ii)
        if rx['return']>0: return rx

        x='"'
        cmd=rx['cut_bat']+'\n'+rs.replace('$#device#$',xtdid)+' '+x+cmd+x

    # Record to tmp batch and run
    rx=ck.gen_tmp_file({'prefix':'tmp-', 'suffix':sext, 'remove_dir':'no'})
    if rx['return']>0: return rx
    fn=rx['file_name']

    rx=ck.save_text_file({'text_file':fn, 'string':cmd})
    if rx['return']>0: return rx

    # Prepare CMD for the host
    y=''
    if sexe!='':
       y+=sexe+' '+fn+envsep
    y+=' '+scall+' '+fn

    if ubtr!='': y=ubtr.replace('$#cmd#$',y)

    y=y+' '+stro+' '+fno+' '+stre+' '+fne

    rx=os.system(y)

    if os.path.isfile(fn):
        os.remove(fn)

    rr={'return':0, 'return_code':rx, 'target_os_dict':tosd}

    # Reading stdout file
    rx=ck.load_text_file({'text_file':fno, 'delete_after_read':'yes', 'split_to_list':stl})
    if rx['return']>0: return rx

    if stl=='yes':
        rr['stdout_lst']=rx['lst']
    else:
        rr['stdout']=rx['string']

    # Reading stderr file
    rx=ck.load_text_file({'text_file':fne, 'delete_after_read':'yes', 'split_to_list':stl})
    if rx['return']>0: return rx
    if stl=='yes':
        rr['stderr_lst']=rx['lst']
    else:
        rr['stderr']=rx['string']

    return rr
