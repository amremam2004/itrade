#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_login_fortuneo.py
#
# Description: Login to fortuneo service
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
#
# Portions created by the Initial Developer are Copyright (C) 2004-2007 the
# Initial Developer. All Rights Reserved.
#
# Contributor(s):
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see http://www.gnu.org/licenses/gpl.html
#
# History       Rev   Description
# 2006-12-31    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
import logging
import re
import os
import httplib
import mimetypes

# iTrade system
import itrade_config
from itrade_logging import *
from itrade_login import *
from itrade_local import message

# ============================================================================
# Login_fortuneo()
#
#   login(user,passwd)
#       store cookie after login
#
#   logout()
#       nop
#
# ============================================================================

class Login_fortuneo(object):
    def __init__(self):
        debug('LiveUpdate_fortuneo:__init__')
        self.m_default_host = "www.fortuneo.fr"
        self.m_login_url =  "/cgi-bin/webact/WebBank/scripts/FRT5.2/loginFRT.jsp"
        self.m_ack_url   =  "/cgi-bin/webact/WebBank/scripts/FRT5.2/mainFRT.jsp"
        self.m_trader_url = "/cgi-bin/webact/WebBank/scripts/FRT5.2/outils/traderQuotes/TraderQuotes.jsp?place_indice=025&plisin=025_FR0000130007&pageAccueil=synthese&BV_SessionID=%s&BV_EngineID=%s"
        self.m_logged = False

        # __x temp
        self.m_username = 'DEMO6C23NH6'
        self.m_password = 'e109'
        self.saveUserInfo()

        debug('Fortuneo login (%s) - ready to run' % self.m_default_host)

    # ---[ properties ] ---

    def name(self):
        return 'fortuneo'

    def desc(self):
        return message('login_fortuneo_desc')

    # ---[ userinfo ] ---
    def saveUserInfo(self):
        f = open(os.path.join(itrade_config.dirUserData,'fortuneo_userinfo.txt'),'w')
        s = self.m_username + ',' + self.m_password
        f.write(s)
        f.close()

    def loadUserInfo(self):
        try:
            f = open(os.path.join(itrade_config.dirUserData,'fortuneo_userinfo.txt'),'r')
        except IOError:
            return False
        s = f.read().strip()
        f.close()
        v = s.split(',')
        if len(v)==2:
            self.m_username = v[0]
            self.m_password = v[1]
            return True
        return False

    # ---[ login ] ---

    def login(self):
        # load username / password
        if not self.loadUserInfo():
            print 'login: userinfo are invalid - please reenter Access Information'
            return False

        # create the HTTPS connexion
        self.m_conn = httplib.HTTPSConnection(self.m_default_host,443)
        if self.m_conn == None:
            print 'login: not connected on %s' % self.m_default_host
            return False

        self.m_logged = False

        params = "sourceB2B=FTO&username=%s&password=%s&pageAccueil=synthese\r\n" % (self.m_username,self.m_password)

        headers = {
                    "Connection":"keep-alive",
                    "Accept":"text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2",
                    "Host":self.m_default_host,
                    "User-Agent":"Mozilla/4.0 (Windows XP 5.1) Java/1.5.0_06",
                    "Pragma":"no-cache",
                    "Cache-Control":"no-cache",
                    "Content-Type":"application/x-www-form-urlencoded"
                    }


        # POST login request
        try:
            self.m_conn.request("POST", self.m_login_url, params, headers)
            flux = self.m_conn.getresponse()
        except:
            print 'Login_fortuneo:POST login failure %s' % self.m_login_url
            return None

        if flux.status != 200:
            print 'Login_fortuneo: login status==%d!=200 reason:%s' % (flux.status,flux.reason)
            return None

        # OK : we are logged to the service ... we can extract Session and Engine ID
        buf = flux.read()
        #print buf

        m = re.search("name=\"BV_SessionID\"\s*value=\"\S+\"",buf,re.IGNORECASE|re.MULTILINE)
        if m==None:
            print 'Login_fortuneo: BV_SessionID statement not found !'
            return None

        BV_SessionID = m.group()[27:-1]

        #print 'BV_SessionID = ',BV_SessionID

        m = re.search("name=\"BV_EngineID\"\s*value=\"\S+\"",buf,re.IGNORECASE|re.MULTILINE)
        if m==None:
            print 'Login_fortuneo: BV_EngineID statement not found !'
            return None

        BV_EngineID = m.group()[26:-1]

        #print 'BV_EngineID = ',BV_EngineID

        # OK ! GOOD ! use BV_SessionID and BV_EngineID to get secure cookie

        # POST ACK
        params = "BV_SessionID=%s&BV_EngineID=%s\r\n" % (BV_SessionID,BV_EngineID)

        try:
            self.m_conn.request("POST", self.m_ack_url, params, headers)
            flux = self.m_conn.getresponse()
        except:
            print 'Login_fortuneo:POST ack failure %s' % self.m_ack_url
            return None

        if flux.status != 200:
            print 'Login_fortuneo: ack status==%d!=200 reason:%s' % (flux.status,flux.reason)
            return None

        buf = flux.read()
        #print buf

        # GET trader request
        try:
            self.m_conn.request("GET", self.m_trader_url % (BV_SessionID,BV_EngineID), None, headers)
            flux = self.m_conn.getresponse()
        except:
            print 'Login_fortuneo:GET trader failure %s' % self.m_trader_url
            return None

        if flux.status != 200:
            print 'Login_fortuneo: trader status==%d!=200 reason:%s' % (flux.status,flux.reason)
            return None

        buf = flux.read()

        # extract cookie
        m = re.search('startStreaming\( \"\S+\",',buf,re.IGNORECASE|re.MULTILINE)
        if m==None:
            print 'Login_fortuneo: cookie statement not found !'
            return None

        cookie = m.group()[17:-11]
        #print len(cookie),':',cookie
        if len(cookie)!=96:
            print 'Login_fortuneo: cookie len is invalid (%d != 96) !' % len(cookie)

        self.m_logged = True

        # save the cookie for later use
        f = open(os.path.join(itrade_config.dirUserData,'fortuneo_live.txt'),'w')
        f.write(cookie)
        f.close()

        self.m_conn.close()

        return True

    def logout(self):
        self.m_logged = False
        return True

    def logged(self):
        return self.m_logged

# ============================================================================
# Export me
# ============================================================================

try:
    ignore(gLoginFortuneo)
except NameError:
    gLoginFortuneo = Login_fortuneo()

registerLoginConnector(gLoginFortuneo.name(),gLoginFortuneo)

# ============================================================================
# Test me
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)

    gLoginFortuneo.login()
    gLoginFortuneo.logout()

# ============================================================================
# That's all folks !
# ============================================================================
