import xbmcaddon
import xbmcgui
import xbmc
import sys
import string
import urllib



_addon_      = xbmcaddon.Addon()
_lang_       = _addon_.getLocalizedString
_addonname_  = _addon_.getAddonInfo('name')
_icon_       = _addon_.getAddonInfo('icon')
_out_path_   = _addon_.getSetting('out_path')
_username_   = _addon_.getSetting('username')
_password_   = _addon_.getSetting('password')

_url_m3u_    = ""
_url_config_ = "http://pastebin.com/raw/pYAFsBZL"

_orig_name_  = "iptvspecial-live.orig.m3u"
_live_name_  = "iptvspecial-live.m3u"
_vod_name_   = "iptvspecial-vod.m3u"
_xxx_name_   = "iptvspecial-xxx.m3u"
_conf_name_  = "iptvspecial.conf"

output_list = list()
output_list_cid = list()





# read config file
def __parse_config_file():
    global _url_m3u_
    
    # update local var with config file content
    file = open(_out_path_ + '/' + _conf_name_, "r")
    cfg_file = file.read()
    file.close()
    
    # generate list with config file rows
    rows = cfg_file.split("\n")
    
    # loop for all rows in config file
    for row in rows:
        row = row.replace('\n', '').replace('\r', '').strip()
        # remove empty rows
        if len(row) > 0:
            # remove comments
            if row[0:1] != "#":
                
                subrow = row.split(";")
                
                # update vars with file content
                output_list.append(subrow[0])

                if len(subrow) > 1:
                    output_list_cid.append(subrow[1].strip())
                    
                else:
                    # error detected
                    xbmcgui.Dialog().notification(_addonname_, _lang_(30006) + subrow[0], xbmcgui.NOTIFICATION_ERROR, 10000)
                    sys.exit(0)
                    
            else:
                # check for url m3u path
                pos = string.find(row, '# URL:')
                if pos == 0:
                    _url_m3u_ = row.replace('# URL:', '').strip()

    # check for url m3u presence    
    if _url_m3u_ == "":
        # no url m3u present
        pbar.close()
        xbmcgui.Dialog().notification(_addonname_, _lang_(30004) + '(url m3u)', xbmcgui.NOTIFICATION_ERROR, 10000)
        sys.exit(0)






# add epg info into live channels list
def __update_live_content():
    # init string for output content
    o_file = ""
    
    # open input file and read all lines
    file = open(_out_path_ + '/' + _orig_name_, "r")
    lines = file.readlines()
    file.close()

    # loop for each line in file
    for line in lines:
        # remove line feed and carriage return
        line = line.replace("\r", "").replace("\n", "")
        
        # check for channel header line
        if string.find(line, '#EXTINF:') == 0:
            # extract channel name
            c_pos = string.find(line, ',')
            c_name = line[c_pos+1:].strip()

            # check for channels group
            if string.find(c_name, '----') == 0:
                # channels group detected
                c_group = c_name.replace('----','').strip()
                o_file += line.replace('#EXTINF:-1', 
                                           '#EXTINF:-1 ' + 
                                           'group-title="' + c_group + '"') + "\n"
            
            else:
                # check for channel presence
                if c_name in output_list:
                    # get cid from config file
                    s_pos = output_list.index(c_name)
                    c_cid = output_list_cid[s_pos]
                    
                    # update line
                    o_file += line.replace('#EXTINF:-1', 
                                           '#EXTINF:-1 ' + 
                                           'tvg-id="' + c_cid + '" ' +
                                           'tvg-logo="' + c_cid + '"') + "\n"
             
                else:
                    # channel not in list, adding
                    o_file += line + "\n"

        else:
            # no channel header, adding
            o_file += line + "\n"
            
    
    return o_file











# show main dialog before start update process
dialog = xbmcgui.Dialog().yesno(_addonname_, _lang_(30001), "", _lang_(30002))

# check for exit
if dialog:
    # update request

    dlfile = urllib.URLopener()
    
    # create progress bar
    pbar = xbmcgui.DialogProgress()
    pbar.create(_addonname_, _lang_(30008))
    pbar.update(10)

    try:
        # try to get config file
        dlfile.retrieve(_url_config_, _out_path_ + '/' + _conf_name_)
        pbar.update(25)
        
    except Exception, ex:
        # error detected
        pbar.close()
        xbmcgui.Dialog().notification(_addonname_, _lang_(30004), xbmcgui.NOTIFICATION_ERROR, 10000)
        sys.exit(0)

    # get config content from file
    __parse_config_file()
    pbar.update(40)


    # update m3u url with user data
    _url_main_ = _url_m3u_.replace('{USERNAME}', _username_)
    _url_main_ = _url_main_.replace('{PASSWORD}', _password_)
    _url_live_ = _url_main_.replace('{TYPE}', 'live')
    _url_vod_  = _url_main_.replace('{TYPE}', 'vod')
    _url_xxx_  = _url_main_.replace('{TYPE}', 'xxx')

    
    try:
        # try to get m3u files
        dlfile.retrieve(_url_live_, _out_path_ + '/' + _orig_name_)
        dlfile.retrieve(_url_vod_,  _out_path_ + '/' + _vod_name_)
        dlfile.retrieve(_url_xxx_,  _out_path_ + '/' + _xxx_name_)
        pbar.update(65)

        # detect file size
        file = open(_out_path_ + '/' + _orig_name_, "r")
        _filesize_ = 1
        if (file.read(1) == ""):
            _filesize_ = 0
        file.close()
        
        
    except Exception, ex:
        # error detected
        pbar.close()
        xbmcgui.Dialog().notification(_addonname_, _lang_(30005), xbmcgui.NOTIFICATION_ERROR, 10000)
        sys.exit(0)
    

    # check for file size = 0 (wrong username password)
    if (_filesize_ == 0):
        # error detected
        pbar.close()
        xbmcgui.Dialog().notification(_addonname_, _lang_(30005), xbmcgui.NOTIFICATION_ERROR, 10000)
        sys.exit(0)

    pbar.update(70, _lang_(30009))

    # update live content
    _new_content_ = __update_live_content()
    pbar.update(90)

    # write new file
    file = open(_out_path_ + '/' + _live_name_, "w")
    file.write(_new_content_)
    file.close()
    
    pbar.close()
    xbmc.executebuiltin('StartPVRManager')

    # update successful
    xbmcgui.Dialog().ok(_addonname_, _lang_(30007))
    
    
else:
    # exit without perform update
    xbmcgui.Dialog().ok(_addonname_, _lang_(30003))
    sys.exit(0)


















