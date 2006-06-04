#!/usr/bin/env python
# ============================================================================
# Project Name : iTrade
# Module Name  : itrade_portfolio.py
#
# Description: Portfolio & Operations
#
# The Original Code is iTrade code (http://itrade.sourceforge.net).
#
# The Initial Developer of the Original Code is	Gilles Dumortier.
#
# Portions created by the Initial Developer are Copyright (C) 2004-2006 the
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
# 2004-02-20    dgil  Wrote it from scratch
# ============================================================================

# ============================================================================
# Imports
# ============================================================================

# python system
from datetime import *
import logging

# iTrade system
from itrade_logging import *
import itrade_datation
from itrade_quotes import quotes,QUOTE_CASH,QUOTE_CREDIT,QUOTE_BOTH
from itrade_matrix import *
from itrade_local import message
import itrade_csv
from itrade_currency import currency2symbol,currencies

# ============================================================================
# Operation
#
#   TYPE:
#       A/B buy (trade)     i.e. accumulate (SRD/x)
#       R/S sell (trade)    i.e. reduce (SRD/x)
#       C   credit (cash)   i.e. deposit
#       D   debit (cash)    i.e. withdrawal
#       F   fee (cash)
#       I   interest (cash)
#       X   split (divisor)
#       Y   detachment of coupon (cash on trade) - non taxable
#       Z   dividend (cash on trade) - taxable
#       L   liquidation     i.e. SRD
#       Q   dividend with shares
#       W   register shares
#
# ============================================================================

OPERATION_BUY       = 'B'
OPERATION_BUY_SRD   = 'A'
OPERATION_SELL      = 'S'
OPERATION_SELL_SRD  = 'R'
OPERATION_CREDIT    = 'C'
OPERATION_DEBIT     = 'D'
OPERATION_FEE       = 'F'
OPERATION_INTEREST  = 'I'
OPERATION_SPLIT     = 'X'
OPERATION_DETACHMENT= 'Y'
OPERATION_DIVIDEND  = 'Z'
OPERATION_LIQUIDATION  = 'L'
OPERATION_QUOTE = 'Q'
OPERATION_REGISTER = 'W'

operation_desc = {
    OPERATION_BUY       : 'Portfolio_buy',
    OPERATION_BUY_SRD   : 'Portfolio_buy_srd',
    OPERATION_SELL      : 'Portfolio_sell',
    OPERATION_SELL_SRD  : 'Portfolio_sell_srd',
    OPERATION_CREDIT    : 'Portfolio_credit',
    OPERATION_DEBIT     : 'Portfolio_debit',
    OPERATION_FEE       : 'Portfolio_fee',
    OPERATION_INTEREST  : 'Portfolio_interest',
    OPERATION_SPLIT     : 'Portfolio_split',
    OPERATION_DETACHMENT: 'Portfolio_detachment',
    OPERATION_DIVIDEND  : 'Portfolio_dividend',
    OPERATION_LIQUIDATION : 'Portfolio_liquidation',
    OPERATION_QUOTE     : 'Portfolio_quote',
    OPERATION_REGISTER  : 'Portfolio_register'
}

operation_cash = {
    OPERATION_BUY       : False,
    OPERATION_BUY_SRD   : False,
    OPERATION_SELL      : False,
    OPERATION_SELL_SRD  : False,
    OPERATION_CREDIT    : True,
    OPERATION_DEBIT     : True,
    OPERATION_FEE       : False,
    OPERATION_INTEREST  : False,
    OPERATION_SPLIT     : False,
    OPERATION_DETACHMENT: False,
    OPERATION_DIVIDEND  : False,
    OPERATION_LIQUIDATION : False,
    OPERATION_REGISTER : False,
    OPERATION_QUOTE : False
}

operation_isin = {
    OPERATION_BUY       : True,
    OPERATION_BUY_SRD   : True,
    OPERATION_SELL      : True,
    OPERATION_SELL_SRD  : True,
    OPERATION_CREDIT    : False,
    OPERATION_DEBIT     : False,
    OPERATION_FEE       : False,
    OPERATION_INTEREST  : False,
    OPERATION_SPLIT     : True,
    OPERATION_DETACHMENT: True,
    OPERATION_DIVIDEND  : True,
    OPERATION_LIQUIDATION  : True,
    OPERATION_REGISTER  : True,
    OPERATION_QUOTE     : True
}

operation_number = {
    OPERATION_BUY       : True,
    OPERATION_BUY_SRD   : True,
    OPERATION_SELL      : True,
    OPERATION_SELL_SRD  : True,
    OPERATION_CREDIT    : False,
    OPERATION_DEBIT     : False,
    OPERATION_FEE       : False,
    OPERATION_INTEREST  : False,
    OPERATION_SPLIT     : False,
    OPERATION_DETACHMENT: False,
    OPERATION_DIVIDEND  : False,
    OPERATION_LIQUIDATION  : True,
    OPERATION_REGISTER  : True,
    OPERATION_QUOTE     : True,
}

operation_sign = {
    OPERATION_BUY       : '-',
    OPERATION_BUY_SRD   : '-',
    OPERATION_SELL      : '+',
    OPERATION_SELL_SRD  : '+',
    OPERATION_CREDIT    : '+',
    OPERATION_DEBIT     : '-',
    OPERATION_FEE       : '-',
    OPERATION_INTEREST  : '+',
    OPERATION_SPLIT     : ' ',
    OPERATION_DETACHMENT: '+',
    OPERATION_DIVIDEND  : '+',
    OPERATION_LIQUIDATION  : '+',
    OPERATION_REGISTER  : '~',
    OPERATION_QUOTE     : ' '
}

operation_apply = {
    OPERATION_BUY       : True,
    OPERATION_BUY_SRD   : True,
    OPERATION_SELL      : True,
    OPERATION_SELL_SRD  : True,
    OPERATION_CREDIT    : False,
    OPERATION_DEBIT     : False,
    OPERATION_FEE       : False,
    OPERATION_INTEREST  : False,
    OPERATION_SPLIT     : False,
    OPERATION_DETACHMENT: True,
    OPERATION_DIVIDEND  : False,
    OPERATION_LIQUIDATION  : True,
    OPERATION_REGISTER  : True,
    OPERATION_QUOTE     : True
}

operation_srd = {
    OPERATION_BUY       : False,
    OPERATION_BUY_SRD   : True,
    OPERATION_SELL      : False,
    OPERATION_SELL_SRD  : True,
    OPERATION_CREDIT    : False,
    OPERATION_DEBIT     : False,
    OPERATION_FEE       : False,
    OPERATION_INTEREST  : False,
    OPERATION_SPLIT     : False,
    OPERATION_DETACHMENT: False,
    OPERATION_DIVIDEND  : False,
    OPERATION_LIQUIDATION  : True,
    OPERATION_REGISTER  : False,
    OPERATION_QUOTE     : False
}

operation_incl_taxes = {
    OPERATION_BUY       : True,
    OPERATION_BUY_SRD   : True,
    OPERATION_SELL      : True,
    OPERATION_SELL_SRD  : True,
    OPERATION_CREDIT    : True,
    OPERATION_DEBIT     : True,
    OPERATION_FEE       : True,
    OPERATION_INTEREST  : True,
    OPERATION_SPLIT     : True,
    OPERATION_DETACHMENT: True,
    OPERATION_DIVIDEND  : True,
    OPERATION_LIQUIDATION  : False,
    OPERATION_REGISTER  : False,
    OPERATION_QUOTE     : True
}

class Operation(object):
    def __init__(self,d,t,m,v,e,n,vat,ref):
        if d[4]=='-':
            debug('Operation::__init__():%s: %d %d %d' % (d,long(d[0:4]),long(d[5:7]),long(d[8:10])));
            self.m_date = date(long(d[0:4]),long(d[5:7]),long(d[8:10]))
        else:
            debug('Operation::__init__():%s: %d %d %d' % (d,long(d[0:4]),long(d[4:6]),long(d[6:8])));
            self.m_date = date(long(d[0:4]),long(d[4:6]),long(d[6:8]))
        self.m_type = t
        self.m_value = float(v)
        self.m_number = long(n)
        self.m_expenses = float(e)
        self.m_vat = float(vat)
        self.m_ref = ref

        # support isin or name or bad value
        if self.isQuote():
            self.m_isin = quotes.lookupTicker(m)
            if self.m_isin:
                self.m_name = self.m_isin.name()
            else:
                self.m_isin = quotes.lookupISIN(m)
                if self.m_isin:
                    self.m_name = self.m_isin.name()
                else:
                    # bad name : keep it :-(
                    self.m_name = m
        else:
            # not a quote : keep the label
            self.m_isin = None
            self.m_name = m

    def __repr__(self):
        if self.m_isin:
            return '%s;%s;%s;%f;%f;%d;%f' % (self.m_date, self.m_type, self.m_isin, self.m_value, self.m_expenses, self.m_number, self.m_vat)
        else:
            return '%s;%s;%s;%f;%f;%d;%f' % (self.m_date, self.m_type, self.m_name, self.m_value, self.m_expenses, self.m_number, self.m_vat)

    def ref(self):
        return self.m_ref

    def nv_value(self):
        return self.m_value

    def sv_value(self):
        return '%.2f' % self.nv_value()

    def nv_expenses(self):
        return self.m_expenses

    def sv_expenses(self):
        return '%.2f' % self.nv_expenses()

    def nv_vat(self):
        return self.m_vat

    def sv_vat(self):
        return '%.2f' % self.nv_vat()

    def nv_number(self):
        if operation_number.has_key(self.m_type) and operation_number[self.m_type]:
            return self.m_number
        else:
            return 0

    def sv_number(self):
        return '%6d' % self.nv_number()

    def type(self):
        return self.m_type

    def isSRD(self):
        if operation_srd.has_key(self.m_type):
            return operation_srd[self.m_type]
        else:
            return False

    def setType(self,nt):
        self.m_type = nt
        return self.m_type

    def name(self):
        return self.m_name

    def date(self):
        return self.m_date

    def sv_date(self):
        return self.date().strftime('%x')

    def setDate(self,nd):
        self.m_date = nd
        return self.m_date

    def isin(self):
        if self.isQuote():
            return self.m_isin
        else:
            raise TypeError("isin(): operation::type() shall be S or B or Y or Z")

    def operation(self):
        if operation_desc.has_key(self.m_type):
            return message(operation_desc[self.m_type])
        else:
            return '? (%s)' % self.m_type

    def isCash(self):
        if operation_cash.has_key(self.m_type):
            return operation_cash[self.m_type]
        return self.isQuote()

    def isQuote(self):
        if operation_isin.has_key(self.m_type):
            return operation_isin[self.m_type]
        else:
            return False

    def sign(self):
        if operation_sign.has_key(self.m_type):
            return operation_sign[self.m_type]
        else:
            return '?'

    def description(self):
        if self.isQuote():
            return '%s (%s)' % (self.name(),self.isin())
        else:
            return self.name()

    def apply(self,d=None):
        if self.m_type == OPERATION_SELL:
            if self.m_isin:
                debug('sell %s' % self.m_isin)
                max = self.m_isin.nv_number(QUOTE_CASH)
                if self.m_number>max:
                    self.m_number = max
                self.m_isin.sell(self.m_number,QUOTE_CASH)
        elif self.m_type == OPERATION_BUY:
            if self.m_isin:
                debug('buy %s' % self.m_isin)
                self.m_isin.buy(self.m_number,self.m_value,QUOTE_CASH)
        elif self.m_type == OPERATION_SELL_SRD:
            if self.m_isin:
                debug('sell SRD %s' % self.m_isin)
                max = self.m_isin.nv_number(QUOTE_CREDIT)
                if self.m_number>max:
                    self.m_number = max
                self.m_isin.sell(self.m_number,QUOTE_CREDIT)
        elif self.m_type == OPERATION_BUY_SRD:
            if self.m_isin:
                debug('buy SRD %s' % self.m_isin)
                self.m_isin.buy(self.m_number,self.m_value,QUOTE_CREDIT)
        elif self.m_type == OPERATION_QUOTE:
            if self.m_isin:
                debug('dividend/shares %s' % self.m_isin)
                self.m_isin.buy(self.m_number,0.0,QUOTE_CASH)
        elif self.m_type == OPERATION_REGISTER:
            if self.m_isin:
                debug('register/shares %s' % self.m_isin)
                self.m_isin.buy(self.m_number,self.m_value,QUOTE_CASH)
        elif self.m_type == OPERATION_DETACHMENT:
            if self.m_isin:
                debug('detachment %s / %d' % (self.m_isin,self.m_value))
                self.m_isin.buy(0,-self.m_value,QUOTE_CASH)
        elif self.m_type == OPERATION_LIQUIDATION:
            if self.m_isin:
                debug('liquidation %s / %d' % (self.m_isin,self.m_value))
                self.m_isin.transfertTo(self.m_number,self.m_expenses,QUOTE_CASH)

    def undo(self,d=None):
        if self.m_type == OPERATION_SELL:
            if self.m_isin:
                debug('undo-sell %s' % self.m_isin)
                self.m_isin.buy(self.m_number,self.m_value,QUOTE_CASH)
        elif self.m_type == OPERATION_BUY:
            if self.m_isin:
                debug('undo-buy %s' % self.m_isin)
                self.m_isin.sell(self.m_number,QUOTE_CASH)
        elif self.m_type == OPERATION_QUOTE:
            if self.m_isin:
                debug('undo-dividend/share %s' % self.m_isin)
                self.m_isin.sell(self.m_number,QUOTE_CASH)
        elif self.m_type == OPERATION_REGISTER:
            if self.m_isin:
                debug('undo-register %s' % self.m_isin)
                self.m_isin.sell(self.m_number,QUOTE_CASH)
        elif self.m_type == OPERATION_BUY_SRD:
            if self.m_isin:
                debug('undo-buy SRD %s' % self.m_isin)
                self.m_isin.sell(self.m_number,QUOTE_CREDIT)
        elif self.m_type == OPERATION_SELL_SRD:
            if self.m_isin:
                debug('undo-sell SRD %s' % self.m_isin)
                self.m_isin.buy(self.m_number,self.m_value,QUOTE_CREDIT)
        elif self.m_type == OPERATION_DETACHMENT:
            if self.m_isin:
                debug('undo-detachment %s' % self.m_isin)
                self.m_isin.buy(0,self.m_value,QUOTE_CASH)
        elif self.m_type == OPERATION_LIQUIDATION:
            if self.m_isin:
                debug('undo-liquidation %s / %d' % self.m_isin)
                self.m_isin.transfertTo(self.m_number,self.m_expenses,QUOTE_CREDIT)

    def nv_pvalue(self):
        if self.m_isin:
            if self.m_type == OPERATION_SELL:
                    return self.m_value - (self.m_isin.nv_pru(QUOTE_CASH) * self.m_number)
            if self.m_type == OPERATION_SELL_SRD:
                    return self.m_value - (self.m_isin.nv_pru(QUOTE_CREDIT) * self.m_number)
        return 0

    def sv_pvalue(self):
        return '%.2f' % self.nv_pvalue()

def isOperationTypeAQuote(type):
    if operation_isin.has_key(type):
        return operation_isin[type]
    else:
        return False

def isOperationTypeIncludeTaxes(type):
    if operation_incl_taxes.has_key(type):
        return operation_incl_taxes[type]
    else:
        return True

def isOperationTypeHasShareNumber(type):
    if operation_number.has_key(type):
        return operation_number[type]
    else:
        return False

def signOfOperationType(type):
    if operation_sign.has_key(type):
        return operation_sign[type]
    else:
        return ' '

# ============================================================================
# Operations : list of Operation
# ============================================================================
#
# CSV File format :
#
#   DATE;TYPE;NAME;VALUE;EXPENSES;NUMBER;VAT
#
#   TYPE: see OPERATION_xx
#
# ============================================================================

class Operations(object):
    def __init__(self,portfolio):
        debug('Operations:__init__(%s)' % portfolio)
        self.m_operations = {}
        self.m_portfolio = portfolio
        self.m_ref = 0

    def portfolio(self):
        return self.m_portfolio

    def list(self):
        items = self.m_operations.values()
        nlist = [(x.date(), x) for x in items]
        nlist.sort()
        nlist = [val for (key, val) in nlist]
        #print nlist
        return nlist

    def load(self,infile=None):
        infile = itrade_csv.read(infile,os.path.join(itrade_config.dirUserData,'default.operations.txt'))
        if infile:
            # scan each line to read each trade
            for eachLine in infile:
                item = itrade_csv.parse(eachLine,7)
                if item:
                    self.add(item,False)

    def save(self,outfile=None):
        itrade_csv.write(outfile,os.path.join(itrade_config.dirUserData,'default.operations.txt'),self.m_operations.values())

    def add(self,item,bApply):
        debug('Operations::add() before: 0:%s , 1:%s , 2:%s , 3:%s , 4:%s , 5:%s' % (item[0],item[1],item[2],item[3],item[4],item[5]))
        #info('Operations::add() before: %s' % item)
        ll = len(item)
        if ll>=7:
            vat = item[6]
        else:
            vat = self.m_portfolio.vat()
        op = Operation(item[0],item[1],item[2],item[3],item[4],item[5],vat,self.m_ref)
        self.m_operations[self.m_ref] = op
        if bApply:
            op.apply()
        debug('Operations::add() after: %s' % self.m_operations)
        self.m_ref = self.m_ref + 1
        return op.ref()

    def remove(self,ref,bUndo):
        if bUndo:
            self.m_operations[ref].undo()
        del self.m_operations[ref]

    def get(self,ref):
        return self.m_operations[ref]

# ============================================================================
# FeeRule
#
# ============================================================================

class FeeRule(object):
    def __init__(self,vfee,vmin,vmax,ref,bPercent=False):
        debug('FeeRule::__init__(): vfee=%.2f vmin=%.2f vmax=%.2f bPercent=%s' %(vfee,vmin,vmax,bPercent))
        self.m_fee = vfee
        self.m_min = vmin
        self.m_max = vmax
        self.m_bPercent = bPercent
        self.m_ref = ref

    def __repr__(self):
        if self.m_bPercent:
            return '%.2f%%;%.2f;%.2f' % (self.m_fee, self.m_min, self.m_max)
        else:
            return '%.2f;%.2f;%.2f' % (self.m_fee, self.m_min, self.m_max)

    def ref(self):
        return self.m_ref

    def nv_fee(self,v):
        if (v>=self.m_min) and (v<=self.m_max):
            if self.m_bPercent:
                return (v*self.m_fee)/100.0
            else:
                return self.m_fee
        else:
            return None

    def sv_fee(self,v):
        n = self.nv_fee(v)
        if n:
            if self.m_bPercent:
                return "%3.2f %%" % (n*100.0)
            else:
                return "%.2f" % n
        else:
            return None

# ============================================================================
# Fees : list of FeeRule
# ============================================================================

class Fees(object):
    def __init__(self,portfolio):
        debug('Fees:__init__(%s)' % portfolio)
        self.m_fees = []
        self.m_portfolio = portfolio
        self.m_ref = 0

    def portfolio(self):
        return self.m_portfolio

    def list(self):
        return self.m_fees.values()

    def load(self,infile=None):
        infile = itrade_csv.read(infile,os.path.join(itrade_config.dirUserData,'default.fees.txt'))
        if infile:
            # scan each line to read each trade
            for eachLine in infile:
                item = itrade_csv.parse(eachLine,3)
                if item:
                    self.addRule(item[0],item[1],item[2])

    def save(self,outfile=None):
        itrade_csv.write(outfile,os.path.join(itrade_config.dirUserData,'default.fees.txt'),self.m_operations.values())

    def addRule(self,sfee,smin,smax):
        debug('Fees::add() before: 0:%s , 1:%s , 2:%s' % (sfee,smin,smax))
        #info('Fees::add() before: %s' % item)
        if sfee[-1:]=='%':
            bPercent = True
            vfee = float(sfee[:-1])
        else:
            bPercent = False
            vfee = float(sfee)
        vmin = float(smin)
        vmax = float(smax)
        fee = FeeRule(vfee,vmin,vmax,self.m_ref,bPercent)
        self.m_fees.append(fee)
        self.m_ref = self.m_ref + 1
        debug('Fees::add() ref=%d after: %s' % (self.m_ref,self.m_fees))
        return self.m_ref

    def removeRule(self,ref):
        del self.m_fees[ref]
        self.m_ref = self.m_ref - 1

    def getRule(self,ref):
        return self.m_fees[ref]

# ============================================================================
# Portfolio
# ============================================================================
#
#   filename
#   name            name displayed for the user
#   accountref      account reference number
#   market          principal market traded by this portfolio
# ============================================================================

class Portfolio(object):
    def __init__(self,filename='default',name='<Portfolio>',accountref='000000000',market='EURONEXT',currency='EUR',vat=1.196):
        debug('Portfolio::__init__ fn=%s name=%s account=%s' % (filename,name,accountref))
        self.m_filename = filename
        self.m_name = name
        self.m_accountref = accountref
        self.m_market = market
        self.m_currency = currency
        self.m_vat = vat
        self._init_()

    def name(self):
        return self.m_name

    def market(self):
        return self.m_market

    def currency(self):
        return self.m_currency

    def vat(self):
        return self.m_vat

    def currency_symbol(self):
        return currency2symbol(self.m_currency)

    def __repr__(self):
        return '%s;%s;%s;%s;%s;%f' % (self.m_filename,self.m_name,self.m_accountref,self.m_market,self.m_currency,self.m_vat)

    def filenamepath(self,portfn,fn):
        return os.path.join(itrade_config.dirUserData,'%s.%s.txt' % (portfn,fn))

    def filepath(self,fn):
        return os.path.join(itrade_config.dirUserData,'%s.%s.txt' % (self.filename(),fn))

    def filename(self):
        return self.m_filename

    def accountref(self):
        return self.m_accountref

    def operations(self):
        return self.m_operations

    def date(self):
        return self.m_date

    def _init_(self):
        self.m_operations = Operations(self)
        self.m_fees = Fees(self)

        # indexed by gCal index
        self.m_inDate = {}          # date
        self.m_inCash = {}          # cash available
        self.m_inCredit = {}        # credit available (SRD)
        self.m_inBuy = {}           # buy
        self.m_inValue = {}         # value available (not including cash)
        self.m_inInvest = {}        # cash investment cumulation
        self.m_inExpenses = {}      # expenses cumulation
        self.m_inTransfer = {}      # transfer cumulation

        # first cell
        self.m_inDate[0] = itrade_datation.gCal.date(0)
        self.m_inCash[0] = 0.0
        self.m_inCredit[0] = 0.0
        self.m_inBuy[0] = 0.0
        self.m_inValue[0] = 0.0
        self.m_inInvest[0] = 0.0
        self.m_inExpenses[0] = 0.0
        self.m_inTransfer[0] = 0.0

        # cumulated value
        self.reset()

    def reinit(self):
        info('Portfolio::%s::reinit' %(self.name()))
        quotes.reinit()
        self._init_()

    def remove(self):
        fn = self.filepath('properties')
        try:
            os.remove(fn)
        except OSError:
            pass
        fn = self.filepath('operations')
        try:
            os.remove(fn)
        except OSError:
            pass
        fn = self.filepath('matrix')
        try:
            os.remove(fn)
        except OSError:
            pass
        fn = self.filepath('fees')
        try:
            os.remove(fn)
        except OSError:
            pass
        fn = self.filepath('stops')
        try:
            os.remove(fn)
        except OSError:
            pass

    def rename(self,nname):
        fn = self.filepath('properties')
        nfn = self.filenamepath(nname,'properties')
        try:
            os.rename(fn,nfn)
        except OSError:
            pass
        fn = self.filepath('operations')
        nfn = self.filenamepath(nname,'operations')
        try:
            os.rename(fn,nfn)
        except OSError:
            pass
        fn = self.filepath('matrix')
        nfn = self.filenamepath(nname,'matrix')
        try:
            os.rename(fn,nfn)
        except OSError:
            pass
        fn = self.filepath('fees')
        nfn = self.filenamepath(nname,'fees')
        try:
            os.rename(fn,nfn)
        except OSError:
            pass
        fn = self.filepath('stops')
        nfn = self.filenamepath(nname,'stops')
        try:
            os.rename(fn,nfn)
        except OSError:
            pass
        self.m_filename = nname

    def reset(self):
        self.m_cCash = 0.0
        self.m_cCredit = 0.0
        self.m_cDIRBuy = 0.0
        self.m_cSRDBuy = 0.0
        self.m_cDIRValue = 0.0
        self.m_cSRDValue = 0.0
        self.m_cInvest = 0.0

        # year dependent
        self.m_cExpenses = 0.0
        self.m_cTransfer = 0.0
        self.m_cTaxable = 0.0
        self.m_cAppreciation = 0.0

    def loadFeesRules(self):
        fn = self.filepath('fees')
        self.m_fees.load(fn)

    def saveFeesRules(self):
        fn = self.filepath('fees')
        self.m_fees.save(fn)

    def applyFeeRules(self,v,all=True):
        fee = 0.0
        for eachFee in self.m_fees.list():
            fee = fee + eachFee.nv_fee(v)
            if fee and all:
                # first rule apply -> return fee
                return fee
        # no rule apply -> no fee
        return fee

    def loadStops(self):
        fn = self.filepath('stops')
        quotes.loadStops(fn)

    def loadProperties(self):
        fn = self.filepath('properties')
        quotes.loadProperties(fn)

    def saveProperties(self):
        fn = self.filepath('properties')
        quotes.saveProperties(fn)

    def loadOperations(self):
        fn = self.filepath('operations')
        self.m_operations.load(fn)

    def saveOperations(self):
        fn = self.filepath('operations')
        self.m_operations.save(fn)

    def applyOperations(self,d=None):
        debug('applyOperations date<=%s' % d)
        for eachOp in self.m_operations.list():
            debug('applyOperations: %s' % eachOp)
            if d==None or d>=eachOp.date():
                typ = eachOp.type()
                if operation_apply.has_key(typ) and operation_apply[typ]:
                    eachOp.apply(d)
            else:
                info('ignore %s' % (eachOp.name()))

    # --- [ manage multi-currency on the portfolio ] ---

    def setupCurrencies(self):
        currencies.reset()
        for eachQuote in quotes.list():
            if eachQuote.isMatrix():
                currencies.inuse(self.m_currency,eachQuote.currency(),bInUse=True)

    def is_multicurrencies(self):
        for eachQuote in quotes.list():
            if eachQuote.isMatrix():
                if eachQuote.currency()!=self.m_currency:
                    return True
        return False

    # --- [ compute the operations ] ---

    def sameyear(self,op,cd=None):
        if cd==None:
            cd = date.today().year
        if cd == op.date().year:
            return True
        else:
            return False

    def computeOperations(self,cd=None):
        self.reset()
        for eachOp in self.m_operations.list():
            if eachOp.type() == OPERATION_CREDIT:
                debug('credit %s : + %f' % (eachOp.name(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash + eachOp.nv_value()
                self.m_cInvest = self.m_cInvest + eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
            elif eachOp.type() == OPERATION_DEBIT:
                debug('debit %s : - %f' % (eachOp.name(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash - eachOp.nv_value()
                # __x self.m_cInvest = self.m_cInvest - eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
            elif eachOp.type() == OPERATION_BUY:
                debug('buy %s/%s : %d for %f' % (eachOp.name(),eachOp.isin(),eachOp.nv_number(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash - eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
            elif eachOp.type() == OPERATION_BUY_SRD:
                debug('buy SRD %s/%s : %d for %f' % (eachOp.name(),eachOp.isin(),eachOp.nv_number(),eachOp.nv_value()))
                self.m_cCredit = self.m_cCredit + eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
            elif eachOp.type() == OPERATION_SELL:
                debug('sell %s/%s : %d for %f' % (eachOp.name(),eachOp.isin(),eachOp.nv_number(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash + eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
                    self.m_cTransfer = self.m_cTransfer + eachOp.nv_value() + eachOp.nv_expenses()
                    self.m_cTaxable = self.m_cTaxable + eachOp.nv_pvalue()
                    self.m_cAppreciation = self.m_cAppreciation + eachOp.nv_pvalue()
            elif eachOp.type() == OPERATION_SELL_SRD:
                debug('sell SRD %s/%s : %d for %f' % (eachOp.name(),eachOp.isin(),eachOp.nv_number(),eachOp.nv_value()))
                self.m_cCredit = self.m_cCredit - eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
                    self.m_cTransfer = self.m_cTransfer + eachOp.nv_value() + eachOp.nv_expenses()
            elif eachOp.type() == OPERATION_FEE:
                debug('fee %s: %f' % (eachOp.name(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash - eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
            elif eachOp.type() == OPERATION_LIQUIDATION:
                debug('liquidation %s: %f' % (eachOp.name(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash + eachOp.nv_value()
                self.m_cCredit = self.m_cCredit + (eachOp.nv_value() + eachOp.nv_expenses())
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
                    self.m_cTaxable = self.m_cTaxable + eachOp.nv_value()
                    self.m_cAppreciation = self.m_cAppreciation + eachOp.nv_value()
                    isin = eachOp.isin()
                    if isin:
                        pv = eachOp.nv_number() * isin.nv_pru(QUOTE_CREDIT)
                        self.m_cTaxable = self.m_cTaxable + pv
                        self.m_cAppreciation = self.m_cAppreciation + pv
            elif eachOp.type() == OPERATION_INTEREST:
                debug('interest %s : %f' % (eachOp.name(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash + eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
                    #self.m_cTaxable = self.m_cTaxable + eachOp.nv_value()
                    self.m_cAppreciation = self.m_cAppreciation + eachOp.nv_value()
            elif eachOp.type() == OPERATION_DETACHMENT:
                debug('detach %s/%s : %f' % (eachOp.name(),eachOp.isin(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash + eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
                    #self.m_cTaxable = self.m_cTaxable + eachOp.nv_value()
                    self.m_cAppreciation = self.m_cAppreciation + eachOp.nv_value()
            elif eachOp.type() == OPERATION_DIVIDEND:
                debug('dividend %s/%s : %f' % (eachOp.name(),eachOp.isin(),eachOp.nv_value()))
                self.m_cCash = self.m_cCash + eachOp.nv_value()
                if self.sameyear(eachOp,cd):
                    self.m_cExpenses = self.m_cExpenses + eachOp.nv_expenses()
                    self.m_cTaxable = self.m_cTaxable + eachOp.nv_value()
                    self.m_cAppreciation = self.m_cAppreciation + eachOp.nv_value()
            elif eachOp.type() == OPERATION_QUOTE:
                debug('dividend/share %s/%s : %f' % (eachOp.name(),eachOp.isin(),eachOp.nv_value()))
                pass
            elif eachOp.type() == OPERATION_REGISTER:
                debug('register/share %s/%s : %f' % (eachOp.name(),eachOp.isin(),eachOp.nv_value()))
                self.m_cInvest = self.m_cInvest + eachOp.nv_value()
            else:
                raise TypeError("computeOperations(): operation::type() unknown %s",eachOp.type())

    # --- [ compute the value ] ---
    def computeValue(self):
        self.m_cDIRValue = 0.0
        self.m_cSRDValue = 0.0
        for eachQuote in quotes.list():
            if eachQuote.isTraded():
                self.m_cDIRValue = self.m_cDIRValue + eachQuote.nv_pv(self.m_currency,QUOTE_CASH)
                self.m_cSRDValue = self.m_cSRDValue + eachQuote.nv_pv(self.m_currency,QUOTE_CREDIT)

    def computeBuy(self):
        self.m_cDIRBuy = 0.0
        self.m_cSRDBuy = 0.0
        for eachQuote in quotes.list():
            if eachQuote.isTraded():
                self.m_cDIRBuy = self.m_cDIRBuy + eachQuote.nv_pr(QUOTE_CASH)
                self.m_cSRDBuy = self.m_cSRDBuy + eachQuote.nv_pr(QUOTE_CREDIT)

    # --- [ operations API ] ---

    def addOperation(self,item):
        self.m_operations.add(item,True)

    def delOperation(self,ref):
        self.m_operations.remove(ref,True)

    def getOperation(self,ref):
        return self.m_operations.get(ref)

    # --- [ value API ] ---
    def nv_cash(self):
        return self.m_cCash

    def nv_credit(self):
        return self.m_cCredit

    def nv_invest(self):
        return self.m_cInvest

    def nv_value(self,box=QUOTE_BOTH):
        # __x compute it !
        self.computeValue()
        if box==QUOTE_CASH:
            return self.m_cDIRValue
        if box==QUOTE_CREDIT:
            return self.m_cSRDValue
        else:
            return self.m_cDIRValue + self.m_cSRDValue

    def nv_buy(self,box=QUOTE_BOTH):
        # __x compute it !
        self.computeBuy()
        if box==QUOTE_CASH:
            return self.m_cDIRBuy
        if box==QUOTE_CREDIT:
            return self.m_cSRDBuy
        else:
            return self.m_cDIRBuy + self.m_cSRDBuy

    def nv_expenses(self):
        return self.m_cExpenses

    def nv_transfer(self):
        return self.m_cTransfer

    def nv_taxable(self):
        if self.m_cTaxable < 0.0:
            return 0.0
        return self.m_cTaxable

    def nv_appreciation(self):
        return self.m_cAppreciation

    def nv_taxes(self):
        if self.nv_transfer() < itrade_config.taxesThreshold:
            return 0.0
        else:
            return self.nv_taxable() * itrade_config.taxesPercent

    def nv_perf(self,box=QUOTE_BOTH):
        #info('nv_perf=%f'% (self.nv_value(box) - self.nv_buy(box)))
        return self.nv_value(box) - self.nv_buy(box)

    def nv_perfPercent(self,box=QUOTE_BOTH):
        n = self.nv_value(box)
        b = self.nv_buy(box)
        if n==0.0 or b==0.0:
            return 0.0
        return ((n*100.0) / b) - 100

    def nv_totalValue(self):
        return self.nv_value(QUOTE_BOTH) + self.nv_cash() - self.m_cCredit

    def nv_perfTotal(self):
        return self.nv_totalValue() - self.nv_invest()

    def nv_perfTotalPercent(self):
        n = self.nv_totalValue()
        i = self.nv_invest()
        if n==0.0 or i==0.0:
            return 0.0
        return ((n*100.0) / i) - 100

    def nv_percentCash(self,box=QUOTE_BOTH):
        total = self.nv_value(box) + self.nv_cash()
        if total==0.0:
            return 0.0
        else:
            return (total-self.nv_value(box))/total*100.0

    def nv_percentQuotes(self,box=QUOTE_BOTH):
        total = self.nv_value(box) + self.nv_cash()
        if total==0.0:
            return 0.0
        else:
            return (total-self.nv_cash())/total*100.0

    # --- [ string API ] ---

    def sv_cash(self,fmt="%.2f"):
        return fmt % self.nv_cash()

    def sv_credit(self,fmt="%.2f"):
        return fmt % self.nv_credit()

    def sv_taxes(self,fmt="%.2f"):
        return fmt % self.nv_taxes()

    def sv_expenses(self,fmt="%.2f"):
        return fmt % self.nv_expenses()

    def sv_transfer(self,fmt="%.2f"):
        return fmt % self.nv_transfer()

    def sv_taxable(self,fmt="%.2f"):
        return fmt % self.nv_taxable()

    def sv_appreciation(self,fmt="%.2f"):
        return fmt % self.nv_appreciation()

    def sv_invest(self,fmt="%.2f"):
        return fmt % self.nv_invest()

    def sv_value(self,box=QUOTE_BOTH,fmt="%.2f"):
        return fmt % self.nv_value(box)

    def sv_buy(self,box=QUOTE_BOTH,fmt="%.2f"):
        return fmt % self.nv_buy(box)

    def sv_perf(self,box=QUOTE_BOTH,fmt="%.2f"):
        return fmt % self.nv_perf(box)

    def sv_perfPercent(self,box=QUOTE_BOTH):
        return "%3.2f %%" % self.nv_perfPercent(box)

    def sv_percentCash(self,box=QUOTE_BOTH):
        return "%3.2f %%" % self.nv_percentCash(box)

    def sv_percentQuotes(self,box=QUOTE_BOTH):
        return "%3.2f %%" % self.nv_percentQuotes(box)

    def sv_totalValue(self):
        return self.nv_totalValue()

    def sv_perfTotal(self):
        return self.nv_perfTotal()

    def sv_perfTotalPercent(self):
        return self.nv_perfTotalPercent()

# ============================================================================
# Portfolios
# ============================================================================
#
# usrdata/portfolio.txt CSV File format :
#   filename;username;accountref
# ============================================================================

class Portfolios(object):
    def __init__(self):
        debug('Portfolios:__init__')
        self._init_()

    def _init_(self):
        self.m_portfolios = {}

    def reinit(self):
        info('Portfolios::reinit')
        for eachPortfolio in self.list():
            eachPortfolio.reinit()

    def list(self):
        return self.m_portfolios.values()

    def existPortfolio(self,fn):
        return self.m_portfolios.has_key(fn)

    def delPortfolio(self,filename):
        if not self.m_portfolios.has_key(filename):
            return False
        else:
            debug('Portfolios::delPortfolio(): %s' % self.m_portfolios[filename])
            self.m_portfolios[filename].remove()
            del self.m_portfolios[filename]
            return True

    def addPortfolio(self,filename,name,accountref,market,currency,vat):
        if self.m_portfolios.has_key(filename):
            return None
        else:
            self.m_portfolios[filename] = Portfolio(filename,name,accountref,market,currency,vat)
            debug('Portfolios::addPortfolio(): %s' % self.m_portfolios[filename])
            return self.m_portfolios[filename]

    def editPortfolio(self,filename,name,accountref,market,currency,vat):
        if not self.m_portfolios.has_key(filename):
            return None
        else:
            del self.m_portfolios[filename]
            self.m_portfolios[filename] = Portfolio(filename,name,accountref,market,currency,vat)
            info('Portfolios::editPortfolio(): %s' % self.m_portfolios[filename])
            return self.m_portfolios[filename]

    def renamePortfolio(self,filename,newfilename):
        if not self.m_portfolios.has_key(filename):
            return None
        else:
            self.m_portfolios[filename].rename(newfilename)
            self.m_portfolios[newfilename] = self.m_portfolios[filename]
            del self.m_portfolios[filename]
            debug('Portfolios::renamePortfolio(): %s -> %s' % (filename,newfilename))
            return self.m_portfolios[newfilename]

    def portfolio(self,fn):
        if self.m_portfolios.has_key(fn):
            return self.m_portfolios[fn]
        else:
            return None

    def load(self,fn=None):
        debug('Portfolios:load()')

        # open and read the file to load these quotes information
        infile = itrade_csv.read(fn,os.path.join(itrade_config.dirUserData,'portfolio.txt'))
        if infile:
            # scan each line to read each portfolio
            for eachLine in infile:
                item = itrade_csv.parse(eachLine,6)
                if item:
                    #debug('%s :: %s' % (eachLine,item))
                    vat = 1.196
                    if len(item)>=5:
                        currency = item[4]
                        if len(item)>=6:
                            vat = float(item[5])
                    else:
                        currency = 'EUR'
                    self.addPortfolio(item[0],item[1],item[2],item[3],currency,vat)

    def save(self,fn=None):
        debug('Portfolios:save()')

        # open and write the file with these quotes information
        itrade_csv.write(fn,os.path.join(itrade_config.dirUserData,'portfolio.txt'),self.m_portfolios.values())

# ============================================================================
# loadPortfolio
#
#   fn    filename reference
# ============================================================================

class currentCell(object):
    def __init__(self,f):
        self.f = f

    def __repr__(self):
        return '%s' % (self.f)

def loadPortfolio(fn=None):
    # default portfolio reference
    if fn==None:
        defref = itrade_csv.read(None,os.path.join(itrade_config.dirUserData,'default.txt'))
        if defref:
            item = itrade_csv.parse(defref[0],1)
            fn = item[0]
        else:
            fn = 'default'
    debug('loadPortfolio %s',fn)

    # create the porfolio
    portfolios.reinit()
    p = portfolios.portfolio(fn)
    if p==None:
        # portfolio does not exist !
        print "Portfolio '%s' does not exist ... create it" % fn
        p = portfolios.addPortfolio(fn,fn,'','EURONEXT','EUR')

    # load properties
    p.loadProperties()

    # load stops
    p.loadStops()

    # load transactions then apply them
    p.loadOperations()
    p.applyOperations()

    # load fees rules
    p.loadFeesRules()

    # save current file
    scf = {}
    scf[0] = currentCell(fn)
    itrade_csv.write(None,os.path.join(itrade_config.dirUserData,'default.txt'),scf.values())

    # return the portfolio
    return p

# ============================================================================
# newPortfolio
#
#   fn    filename reference (shall be unique)
# ============================================================================

def newPortfolio(fn=None):
    debug('newPortfolio %s',fn)

# ============================================================================
# CommandLine : -e / evaluate portfolio
# ============================================================================

def cmdline_evaluatePortfolio(year=2006):

    print '--- load current portfolio ---'
    p = loadPortfolio()
    print '... %s:%s:%s ' % (p.filename(),p.name(),p.accountref())

    print '--- build a matrix -----------'
    m = createMatrix(p.filename(),p)

    print '--- liveupdate this matrix ---'
    m.update()
    m.saveTrades()

    print '--- evaluation ---------------'
    p.computeOperations(year)
    print ' cumul. investment  : %.2f' % p.nv_invest()
    print
    print ' total buy          : %.2f' % p.nv_buy(QUOTE_CASH)
    print ' evaluation quotes  : %.2f (%2.2f%% of portfolio)' % (p.nv_value(QUOTE_CASH),p.nv_percentQuotes(QUOTE_CASH))
    print ' evaluation cash    : %.2f (%2.2f%% of portfolio)' % (p.nv_cash(),p.nv_percentCash(QUOTE_CASH))
    print ' performance        : %.2f (%2.2f%%)' % (p.nv_perf(QUOTE_CASH),p.nv_perfPercent(QUOTE_CASH))
    print
    print ' total credit (SRD) : %.2f (==%.2f)' % (p.nv_credit(),p.nv_buy(QUOTE_CREDIT))
    print ' evaluation quotes  : %.2f (%2.2f%% of portfolio)' % (p.nv_value(QUOTE_CREDIT),p.nv_percentQuotes(QUOTE_CREDIT))
    print ' evaluation cash    : %.2f (%2.2f%% of portfolio)' % (p.nv_cash(),p.nv_percentCash(QUOTE_CREDIT))
    print ' performance        : %.2f (%2.2f%%)' % (p.nv_perf(QUOTE_CREDIT),p.nv_perfPercent(QUOTE_CREDIT))
    print
    print ' expenses (VAT, ...): %.2f' % p.nv_expenses()
    print ' total of transfers : %.2f' % p.nv_transfer()
    print ' appreciation       : %.2f' % p.nv_appreciation()
    print ' taxable amount     : %.2f' % p.nv_taxable()
    print ' amount of taxes    : %.2f' % p.nv_taxes()
    print
    print ' evaluation total   : %.2f ' % p.nv_totalValue()
    print ' global performance : %.2f (%2.2f%%)' % (p.nv_perfTotal(),p.nv_perfTotalPercent())

    return (p,m)

# ============================================================================
# Export
# ============================================================================

try:
    ignore(portfolios)
except NameError:
    portfolios = Portfolios()

portfolios.load()

# ============================================================================
# Test
# ============================================================================

if __name__=='__main__':
    setLevel(logging.INFO)
    cmdline_evaluatePortfolio(2006)

# ============================================================================
# That's all folks !
# ============================================================================
# vim:set shiftwidth=4 tabstop=8 expandtab textwidth=78:
