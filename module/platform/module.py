#
# Collective Knowledge (platform detection)
#
# See CK LICENSE.txt for licensing details
# See CK Copyright.txt for copyright details
#
# Developer: Grigori Fursin, Grigori.Fursin@cTuning.org, http://cTuning.org/lab/people/gfursin
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
# collect info about platforms

def detect(i):
    """
    Input:  {
              (host_os)              - host OS (detect, if omitted)
              (os) or (target_os)    - OS module to check (if omitted, analyze host)

              (device_id)            - device id if remote (such as adb)
              (skip_device_init)     - if 'yes', do not initialize device
              (print_device_info)    - if 'yes', print extra device info

              (skip_info_collection) - if 'yes', do not collect info (particularly for remote)

              (exchange)             - if 'yes', exchange info with some repo (by default, remote-ck)
              (exchange_repo)        - which repo to record/update info (remote-ck by default)
              (exchange_subrepo)     - if remote, remote repo UOA
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              host_os_uoa                 - host OS UOA
              host_os_uid                 - host OS UID
              host_os_dict                - host OS meta

              os_uoa                      - target OS UOA
              os_uid                      - target OS UID
              os_dict                     - target OS meta

              (devices)                   - return devices if device_id==''
              (device_id)                 - if device_id=='' and only 1 device, select it

              cpu_properties_unified      - CPU properties, unified
              cpu_properties_all          - assorted CPU properties, platform dependent

              os_properties_unified       - OS properties, unified
              os_properties_all           - assorted OS properties, platform dependent

              platform_properties_unified - platform properties, unified
              platform_properties_all     - assorted platform properties, platform dependent

              acc_properties_unified      - Accelerator properties, unified
              acc_properties_all          - assorted Accelerator properties, platform dependent
            }

    """

    import os

    o=i.get('out','')

    oo=''
    if o=='con': oo=o

    # Various params
    hos=i.get('host_os','')
    tos=i.get('target_os','')
    if tos=='': tos=i.get('os','')
    tdid=i.get('device_id','')

    sic=i.get('skip_info_collection','')
    sdi=i.get('skip_device_init','')
    pdv=i.get('print_device_info','')
    ex=i.get('exchange','')

    # Get OS info
    import copy
    ii=copy.deepcopy(i)
    ii['out']=oo
    ii['action']='detect'
    ii['module_uoa']=cfg['module_deps']['platform.cpu']
    rr=ck.access(ii) # DO NOT USE rr further - will be reused as return !
    if rr['return']>0: return rr

    hos=rr['host_os_uid']
    hosx=rr['host_os_uoa']
    hosd=rr['host_os_dict']

    tos=rr['os_uid']
    tosx=rr['os_uoa']
    tosd=rr['os_dict']

    tbits=tosd.get('bits','')

    tdid=rr['device_id']

    # Some params
    ro=tosd.get('redirect_stdout','')
    remote=tosd.get('remote','')
    win=tosd.get('windows_base','')

    dv=''
    if tdid!='': dv='-s '+tdid

    # Init
    prop={}
    prop_all={}

    xos=rr['os_uoa']
    device_id=rr['device_id']

    os_uoa=rr['os_uoa']
    os_uid=rr['os_uid']
    os_dict=rr['os_dict']

    remote=os_dict.get('remote','')
    os_win=os_dict.get('windows_base','')

    ro=os_dict.get('redirect_stdout','')

    # Get accelerator info (GPU, etc.)
    import copy
    ii=copy.deepcopy(i)
    ii['out']=oo
    ii['action']='detect'
    ii['module_uoa']=cfg['module_deps']['platform.accelerator']
    rx=ck.access(ii) # DO NOT USE rr further - will be reused as return !
    if rx['return']>0: return rr
    rr.update(rx)

    # Get info about system ######################################################
    remote=os_dict.get('remote','')
    if remote=='yes':
       params={}

       rx=ck.gen_tmp_file({'prefix':'tmp-ck-'})
       if rx['return']>0: return rx
       fn=rx['file_name']

       x=tosd.get('adb_all_params','')
       x=x.replace('$#redirect_stdout#$', ro)
       x=x.replace('$#output_file#$', fn)

       dv=''
       if tdid!='': dv='-s '+tdid
       x=x.replace('$#device#$',dv)

       if o=='con' and pdv=='yes':
          ck.out('')
          ck.out('Receiving all parameters:')
          ck.out('  '+x)

       rx=os.system(x)
       if rx!=0:
          if o=='con':
             ck.out('')
             ck.out('Non-zero return code :'+str(rx)+' - likely failed')
          return {'return':1, 'error':'access to remote device failed'}

       # Read and parse file
       rx=ck.load_text_file({'text_file':fn, 'split_to_list':'yes', 'delete_after_read':'yes'})
       if rx['return']>0: return rx
       ll=rx['lst']

       for s in ll:
           s1=s.strip()

           q2=s1.find(']: [')
           k=''
           if q2>=0:
              k=s1[1:q2].strip()
              v=s1[q2+4:].strip()
              v=v[:-1].strip()

              params[k]=v

       prop_all['adb_params']=params

#       for q in params:
#           v=params[q]
#           print q+'='+v

       model=params.get('ro.product.model','')
       manu=params.get('ro.product.manufacturer','')
       if model!='' and manu!='':
          if model.lower().startswith(manu.lower()):
             model=model[len(manu)+1:]

       prop['system_name']=manu+' '+model
       prop['model']=model
       prop['vendor']=manu
    else:
       x1=''
       x2=''

       target_system_model=''
       target_system_name=''

       if os_win=='yes':
          r=get_from_wmic({'group':'csproduct'})
          if r['return']>0: return r
          info1=r['dict']

          x1=info1.get('Vendor','')
          x2=info1.get('Version','')

          target_system_name=x1+' '+x2

          r=get_from_wmic({'cmd':'computersystem get model'})
          if r['return']>0: return r
          target_system_model=r['value']

          prop_all['cs_product']=info1
       else:
          file_with_vendor='/sys/devices/virtual/dmi/id/sys_vendor'
          if os.path.isfile(file_with_vendor):
             r=ck.load_text_file({'text_file':file_with_vendor})
             if r['return']>0: return r
             x1=r['string'].strip()

          file_with_version='/sys/devices/virtual/dmi/id/product_version'
          if os.path.isfile(file_with_version):
             r=ck.load_text_file({'text_file':file_with_version})
             if r['return']>0: return r
             x2=r['string'].strip()

          if x1!='' and x2!='':
             target_system_name=x1+' '+x2

          file_with_id='/sys/devices/virtual/dmi/id/product_name'
          if os.path.isfile(file_with_id):
             r=ck.load_text_file({'text_file':file_with_id})
             if r['return']>0: return r
             target_system_model=r['string'].strip()

       prop['vendor']=x1
       prop['system_name']=target_system_name
       prop['model']=target_system_model


    if o=='con':
       ck.out('')
       ck.out('Platform vendor: '+prop.get('vendor',''))
       ck.out('Platform name:   '+prop.get('system_name',''))
       ck.out('Platform model:  '+prop.get('model',''))

    rr['platform_properties_unified']=prop
    rr['platform_properties_all']=prop_all

    return rr

##############################################################################
# Get info from WMIC on Windows

def get_from_wmic(i):
    """
    Input:  {
              cmd     - cmd for wmic
              (group) - get the whole group
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              value        - obtained value
              (dict)       - if group
            }

    """

    import os

    value=''
    dd={}

    rx=ck.gen_tmp_file({'prefix':'tmp-ck-'})
    if rx['return']>0: return rx
    fn=rx['file_name']

    xcmd=i.get('cmd','')
    xgroup=i.get('group','')
    if xgroup!='': xcmd=xgroup

    cmd='wmic '+xcmd+' > '+fn
    r=os.system(cmd)
    if r!=0:
       return {'return':1, 'error':'command returned non-zero value: '+cmd}

    # Read and parse file
    rx=ck.load_text_file({'text_file':fn, 'encoding':'utf16', 'split_to_list':'yes'})
    if rx['return']>0: return rx
    ll=rx['lst']

    if os.path.isfile(fn): os.remove(fn)

    if xgroup=='':
       if len(ll)>1:
          value=ll[1].strip()
    else:
       if len(ll)>1:
          kk=ll[0]
          value=ll[1]

          xkeys=kk.split(' ')
          keys=[]
          for q in xkeys:
              if q!='': keys.append(q)

          for q in range(0, len(keys)):
              k=keys[q]

              if q==0: qx=0
              else: 
                 y=' '
                 if q==len(keys)-1: y=''
                 qx=kk.find(' '+k+y)

              if q==len(keys)-1:
                 qe=len(value)
              else:
                 qe=kk.find(' '+keys[q+1]+' ')

              v=value[qx:qe].strip()
              dd[k]=v

    return {'return':0, 'value':value, 'dict':dd}

##############################################################################
# Init remote device

def init_device(i):
    """
    Input:  {
              os_dict      - OS dict to get info about how to init device
              device_id    - ID of the device if more than one
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """

    import os

    o=i.get('out','')

    osd=i['os_dict']
    tdid=i['device_id'].strip()

    ri=osd.get('remote_init','')
    if ri!='':
       if o=='con':
          ck.out('Initializing remote device:')
          ck.out('  '+ri)
          ck.out('')

       dv=''
       if tdid!='': dv='-s '+tdid
       ri=ri.replace('$#device#$',dv)

       rx=os.system(ri)
       if rx!=0:
          if o=='con':
             ck.out('')
             ck.out('Non-zero return code :'+str(rx)+' - likely failed')
          return {'return':1, 'error':'remote device initialization failed'}

       device_init='yes'

    return {'return':0}
